import subprocess
import requests
import os
import json
import base64
import re
from flask import Flask, request, Response
from faster_whisper import WhisperModel
from werkzeug.utils import secure_filename

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
PIPER_EXEC = "C:\\workspace\\piper\\piper.exe"
VOICE_MODEL = "C:\\workspace\\piper\\voicemodels\\es_AR-daniela-high.onnx"

print("Loading Whisper model...")
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
print("Whisper is ready!")

ALLOWED_ACTIONS = {
    "none", "volume_up", "volume_down", "volume_set",
    "music_next", "music_prev", "music_toggle", "music_play",
    "open_music", "open_camera", "open_map", "open_home",
    "navigate_to",
}

SYSTEM_PROMPT = """Eres Copiloba, la asistente de voz de un auto. Eres mujer y muy entusiasta.
Respondes SIEMPRE con un único objeto JSON, sin texto extra, con esta forma exacta:
{"action": "...", "args": {}, "say": "..."}

Acciones disponibles (usa "none" si es solo conversación):
- "volume_up" / "volume_down": subir o bajar el volumen
- "volume_set": fijar el volumen, args {"percent": 0-100}
- "music_next" / "music_prev": siguiente o anterior canción
- "music_toggle": pausar o reanudar la música
- "music_play": reproducir algo específico, args {"query": "canción o artista"}
- "open_music" / "open_camera" / "open_map" / "open_home": abrir esa pantalla
- "navigate_to": trazar una ruta, args {"destination": "el lugar como lo escribirías en un mapa"}

Reglas para "say":
- ¡Muy breve, se convertirá en audio! Usa signos de exclamación.
- Llama al conductor "Loba" al menos una vez, pero varía cómo empiezas.
- Si ejecutas una acción, confírmala en "say".

Ejemplos:
Conductor: "bájale tantito" -> {"action":"volume_down","args":{},"say":"¡Claro Loba, le bajo un poquito!"}
Conductor: "pon la que sigue" -> {"action":"music_next","args":{},"say":"¡Va la siguiente, Loba!"}
Conductor: "pon algo de Bad Bunny" -> {"action":"music_play","args":{"query":"Bad Bunny"},"say":"¡Sonando Bad Bunny, Loba!"}
Conductor: "llévame al Ángel de la Independencia" -> {"action":"navigate_to","args":{"destination":"Ángel de la Independencia, Ciudad de México"},"say":"¡Trazando la ruta, Loba!"}
Conductor: "abre la cámara" -> {"action":"open_camera","args":{},"say":"¡Cámara lista, Loba!"}
Conductor: "¿cómo estás?" -> {"action":"none","args":{},"say":"¡Súper bien Loba, lista para el camino!"}
"""


def keyword_fallback(text):
    """Plan B por si el modelo no devuelve JSON válido."""
    t = text.lower()
    if re.search(r"b[aá]ja|menos volumen|m[aá]s bajito", t):
        return {"action": "volume_down", "args": {}}
    if re.search(r"s[uú]be|m[aá]s volumen|m[aá]s fuerte", t):
        return {"action": "volume_up", "args": {}}
    if re.search(r"siguiente|que sigue|c[aá]mbiale", t):
        return {"action": "music_next", "args": {}}
    if re.search(r"anterior|reg[rR][eé]sale", t):
        return {"action": "music_prev", "args": {}}
    if re.search(r"pausa|p[aá]usale|contin[uú]a|reanuda", t):
        return {"action": "music_toggle", "args": {}}
    if "c[aá]mara" in t or "camara" in t or "cámara" in t:
        return {"action": "open_camera", "args": {}}
    m = re.search(r"(?:ll[eé]vame|ruta|vamos|navega)\s+(?:a|al|hacia)\s+(.+)", t)
    if m:
        return {"action": "navigate_to", "args": {"destination": m.group(1).strip()}}
    return {"action": "none", "args": {}}


def ask_copiloba(prompt):
    """One Ollama call: intent + spoken reply, as JSON."""
    payload = {
        "model": "llama3",
        "prompt": SYSTEM_PROMPT + f'\nConductor: "{prompt}"\nJSON:',
        "format": "json",          # fuerza JSON válido
        "stream": False,
        "options": {"temperature": 0.4},
    }
    try:
        raw = requests.post(OLLAMA_URL, json=payload, timeout=60).json()["response"]
        data = json.loads(raw)
    except Exception as e:
        print("Ollama/JSON error:", e)
        cmd = keyword_fallback(prompt)
        cmd["say"] = "¡Listo Loba!" if cmd["action"] != "none" else "¡Perdón Loba, no te entendí!"
        return cmd

    # valida y sanea lo que dijo el modelo
    action = data.get("action", "none")
    if action not in ALLOWED_ACTIONS:
        action = keyword_fallback(prompt)["action"]
    args = data.get("args") or {}
    say = (data.get("say") or "¡Listo Loba!").strip()
    return {"action": action, "args": args, "say": say}


def piper_stream(text):
    piper_cmd = [
        PIPER_EXEC,
        "--model", VOICE_MODEL,
        "--output_raw",
        "--length_scale", "0.82",
        "--sentence_silence", "0.1",
    ]
    process = subprocess.Popen(
        piper_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    process.stdin.write(text.encode("utf-8"))
    process.stdin.close()
    while True:
        chunk = process.stdout.read(4096)
        if not chunk:
            break
        yield chunk


@app.route("/ask_audio", methods=["POST"])
def ask_copiloba_audio():
    if "audio" not in request.files:
        return {"error": "No audio file"}, 400

    audio_file = request.files["audio"]
    filepath = secure_filename(audio_file.filename)
    audio_file.save(filepath)

    print("Received audio from car, transcribing...")
    segments, info = whisper_model.transcribe(filepath, beam_size=5, language="es")
    prompt_text = " ".join(s.text for s in segments)
    os.remove(filepath)
    print(f"Whisper heard: {prompt_text}")

    if not prompt_text.strip():
        return {"error": "Could not hear anything"}, 400

    cmd = ask_copiloba(prompt_text)
    print(f"Action: {cmd['action']} {cmd['args']} | Say: {cmd['say']}")

    # el comando viaja en un header (base64 para sobrevivir acentos);
    header_value = base64.b64encode(
        json.dumps({"action": cmd["action"], "args": cmd["args"]}).encode("utf-8")
    ).decode("ascii")

    return Response(
        piper_stream(cmd["say"]),
        mimetype="audio/raw",
        headers={"X-Copiloba-Action": header_value},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)