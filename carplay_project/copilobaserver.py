import subprocess
import requests
import os
from flask import Flask, request, Response
from faster_whisper import WhisperModel
from werkzeug.utils import secure_filename

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
PIPER_EXEC = "C:\\workspace\\piper\\piper.exe"
VOICE_MODEL = "C:\\workspace\\piper\\voicemodels\\es_AR-daniela-high.onnx"

# Load Whisper model into PC memory (Use 'base' or 'small' for speed)
print("Loading Whisper model...")
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
print("Whisper is ready!")

def generate_audio_stream(prompt):
    """Generator that yields audio bytes as they are created."""
    print(f"Received prompt from car: {prompt}")

    # 1. Ask Ollama for the text response
    ollama_payload = {
        "model": "llama3",
        "prompt": (
            "Eres Copiloba, una asistente de vehículo, eres mujer. "
            "¡Usa siempre signos de exclamación (¡!) en tus oraciones para sonar emocionada! "
            "Sé muy breve, tu texto se transformará en audio. "
            "Refiérete al conductor como 'Loba', nunca olvídes llamarle loba por lo menos una vez. "
            "No siempre empieces tus respuestas diciendo 'Hola loba', varía."
            f"El conductor dice: {prompt}"
        ),
        "stream": False
    }

    # Make sure Ollama is running on Windows!
    ollama_res = requests.post(OLLAMA_URL, json=ollama_payload).json()
    response_text = ollama_res['response']
    print(f"Ollama generated: {response_text}")

    # 2. Run Piper directly (No shell=True, no 'echo')
    # We pass the arguments as a Python list. This is 100% safe on Windows.
    # 2. Run Piper directly with energetic pacing parameters
    piper_cmd = [
        PIPER_EXEC,
        "--model", VOICE_MODEL,
        "--output_raw",
        "--length_scale", "0.82",  # Speeds up the voice (try 0.8 to 0.9)
        "--sentence_silence", "0.1"  # Removes the long, awkward pauses between sentences
    ]

    process = subprocess.Popen(
        piper_cmd,
        stdin=subprocess.PIPE,  # Open a pipe to push text IN
        stdout=subprocess.PIPE,  # Open a pipe to pull audio OUT
        stderr=subprocess.DEVNULL
    )

    # 3. Safely push the UTF-8 Spanish text directly into Piper's memory
    process.stdin.write(response_text.encode('utf-8'))
    process.stdin.close()  # Close the input pipe so Piper knows we finished typing

    # 4. Stream the raw audio bytes back to the STM32 board instantly
    while True:
        chunk = process.stdout.read(4096)
        if not chunk:
            break
        yield chunk


@app.route('/ask_audio', methods=['POST'])
def ask_copiloba_audio():
    # 1. Receive the .wav file from the car
    if 'audio' not in request.files:
        return {"error": "No audio file"}, 400

    audio_file = request.files['audio']
    filepath = secure_filename(audio_file.filename)
    audio_file.save(filepath)

    print("Received audio from car, transcribing...")

    # 2. Whisper translates Spanish audio to text
    segments, info = whisper_model.transcribe(filepath, beam_size=5, language="es")
    prompt_text = " ".join([segment.text for segment in segments])

    print(f"Whisper heard: {prompt_text}")

    # Clean up the file
    os.remove(filepath)

    if not prompt_text.strip():
        return {"error": "Could not hear anything"}, 400

    # 3. Stream the response back using your existing function
    return Response(generate_audio_stream(prompt_text), mimetype="audio/raw")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)