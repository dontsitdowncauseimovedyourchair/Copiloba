"""
voice/assistant.py — Copiloba Voice Assistant Pipeline
Architecture: Microphone → Whisper.cpp → Claude API → Piper → PipeWire

Design constraints (STM32MP25 ARM64):
- No heavy Python audio libs (no pyaudio, sounddevice).
  Uses arecord (ALSA) to write WAV, then reads it.
- Whisper.cpp is called as a subprocess — avoids loading model in Python.
- Claude API via requests (already a dep), NOT the anthropic SDK,
  to avoid pulling in httpx/anyio on embedded.
- Piper TTS via subprocess → writes WAV → pw-play via subprocess.
- All blocking work runs in daemon threads.
  GTK is only touched through GLib.idle_add().
"""

import os
import json
import subprocess
import threading
import requests
from gi.repository import GLib

# ── Configuration ────────────────────────────────────────────────────────────

WHISPER_BIN   = "/usr/local/bin/whisper-cli"          # whisper.cpp CLI binary
WHISPER_MODEL = "/home/root/models/ggml-tiny.bin"     # smallest viable model
PIPER_BIN     = "/usr/local/bin/piper"
PIPER_VOICE   = "/home/root/tts/es_MX-claude-medium.onnx"
PIPER_CONFIG  = "/home/root/tts/es_MX-claude-medium.onnx.json"

# arecord settings — adjust device name with `arecord -l` on target
ARECORD_DEVICE = "default"       # or "hw:1,0" for a specific USB mic
RECORD_SECONDS = 6               # max recording length per press
RECORD_WAV     = "/tmp/copiloba_rec.wav"
TTS_WAV        = "/tmp/copiloba_tts.wav"

# Claude API — model pinned to claude-haiku for lowest latency on embedded
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL   = "claude-haiku-4-5-20251001"
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# System prompt — instructs Claude to return JSON for commands, plain text
# for conversation.  Kept short to minimise token count (= lower latency).
SYSTEM_PROMPT = """Eres Copiloba, el asistente de voz de un sistema CarPlay embebido.
Responde SIEMPRE en español.
Cuando el usuario pida navegar entre pantallas o controlar música, responde
ÚNICAMENTE con un objeto JSON válido (sin markdown, sin backticks), así:
  {"type":"command","action":"open_music"}
  {"type":"command","action":"open_camera"}
  {"type":"command","action":"open_home"}
  {"type":"command","action":"open_map"}
  {"type":"command","action":"pause_music"}
  {"type":"command","action":"resume_music"}
  {"type":"command","action":"next_track"}
  {"type":"command","action":"prev_track"}
Para cualquier otra petición o conversación, responde con texto plano breve
(máximo 2 oraciones).  NO uses markdown ni listas."""


class VoiceAssistant:
    """
    Manages the full voice pipeline.
    Instantiate once and hold a reference in CarPlayWindow.

    Public API:
        assistant.start_recording()   — call on mic button press
        assistant.stop_recording()    — call on mic button release (or timeout)

    Callbacks set by the owner:
        assistant.on_state_change(state: str)
            states: "idle" | "recording" | "transcribing" | "thinking" | "speaking"
        assistant.on_command(action: str)
            called when Claude returns a navigation/control command
        assistant.on_error(msg: str)
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._recording_proc = None   # arecord subprocess handle
        self._busy = False            # True while pipeline is running

        self.on_state_change = lambda s: None
        self.on_command      = lambda a: None
        self.on_error        = lambda m: None

    # ── Public ──────────────────────────────────────────────────────────────

    def start_recording(self):
        """Start mic capture. Returns immediately; capture runs in a thread."""
        with self._lock:
            if self._busy:
                return
            self._busy = True

        self._set_state("recording")
        t = threading.Thread(target=self._record_task, daemon=True)
        t.start()

    def stop_recording(self):
        """Signal arecord to stop early (user released button)."""
        with self._lock:
            proc = self._recording_proc
        if proc and proc.poll() is None:
            proc.terminate()   # arecord exits cleanly on SIGTERM, flushes WAV

    # ── Internal pipeline ────────────────────────────────────────────────────

    def _record_task(self):
        """Stage 1: record audio with arecord into a WAV file."""
        try:
            cmd = [
                "arecord",
                "-D", ARECORD_DEVICE,
                "-f", "S16_LE",     # 16-bit signed little-endian
                "-r", "16000",      # 16 kHz — Whisper's native rate
                "-c", "1",          # mono
                "-d", str(RECORD_SECONDS),
                RECORD_WAV,
            ]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            with self._lock:
                self._recording_proc = proc
            proc.wait()
        except Exception as e:
            self._fail(f"arecord error: {e}")
            return
        finally:
            with self._lock:
                self._recording_proc = None

        # Check the WAV has content (> 44 bytes header)
        try:
            size = os.path.getsize(RECORD_WAV)
        except OSError:
            size = 0
        if size < 1000:
            self._fail("No se grabó audio (micrófono no disponible)")
            return

        self._transcribe_task()

    def _transcribe_task(self):
        """Stage 2: run whisper.cpp on the recorded WAV."""
        self._set_state("transcribing")
        try:
            cmd = [
                WHISPER_BIN,
                "-m", WHISPER_MODEL,
                "-f", RECORD_WAV,
                "-l", "es",         # force Spanish language
                "--no-timestamps",
                "-nt",              # no timestamps in output
                "--output-txt",     # write to RECORD_WAV.txt
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,         # generous for embedded CPU
            )
            text = result.stdout.strip()

            # whisper-cli also supports -otxt which writes <file>.txt
            # Try reading that file as fallback if stdout is empty
            if not text:
                txt_path = RECORD_WAV + ".txt"
                if os.path.exists(txt_path):
                    with open(txt_path) as f:
                        text = f.read().strip()

            text = text.strip()
            if not text or text.lower() in {"", "[blank_audio]", "(blank)"}:
                self._fail("No se detectó voz")
                return

        except subprocess.TimeoutExpired:
            self._fail("Whisper tardó demasiado")
            return
        except Exception as e:
            self._fail(f"Whisper error: {e}")
            return

        self._claude_task(text)

    def _claude_task(self, user_text):
        """Stage 3: send transcribed text to Claude API."""
        self._set_state("thinking")
        if not CLAUDE_API_KEY:
            self._fail("ANTHROPIC_API_KEY no configurada")
            return
        try:
            payload = {
                "model": CLAUDE_MODEL,
                "max_tokens": 256,   # keep small; responses must be short
                "system": SYSTEM_PROMPT,
                "messages": [
                    {"role": "user", "content": user_text}
                ],
            }
            headers = {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            resp = requests.post(
                CLAUDE_API_URL,
                json=payload,
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["content"][0]["text"].strip()

        except requests.exceptions.Timeout:
            self._fail("Claude no respondió a tiempo")
            return
        except Exception as e:
            self._fail(f"Claude API error: {e}")
            return

        self._route_and_speak(reply)

    def _route_and_speak(self, reply):
        """Stage 4: parse reply, fire command or speak it."""
        # Try to parse as a command JSON
        try:
            obj = json.loads(reply)
            if obj.get("type") == "command":
                action = obj.get("action", "")
                GLib.idle_add(self.on_command, action)
                # Speak a brief confirmation
                confirmations = {
                    "open_music":  "Abriendo Spotify",
                    "open_camera": "Abriendo la cámara",
                    "open_home":   "Volviendo al inicio",
                    "open_map":    "Abriendo el mapa",
                    "pause_music": "Pausando la música",
                    "resume_music":"Reanudando la música",
                    "next_track":  "Siguiente canción",
                    "prev_track":  "Canción anterior",
                }
                speech_text = confirmations.get(action, "Listo")
                self._speak_task(speech_text)
                return
        except (json.JSONDecodeError, TypeError, KeyError):
            pass  # not a command — treat as plain speech

        # Plain conversational response
        self._speak_task(reply)

    def _speak_task(self, text):
        """Stage 5: synthesise speech with Piper, play with pw-play."""
        self._set_state("speaking")
        try:
            # Piper reads from stdin, writes WAV to stdout
            piper_cmd = [
                PIPER_BIN,
                "--model", PIPER_VOICE,
                "--config", PIPER_CONFIG,
                "--output_file", TTS_WAV,
            ]
            proc = subprocess.run(
                piper_cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=20,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"piper exited {proc.returncode}: {proc.stderr.decode()}")

            # Play through PipeWire
            play_cmd = ["pw-play", TTS_WAV]
            subprocess.run(play_cmd, timeout=30)

        except Exception as e:
            # Non-fatal: speech failed but command may have already fired
            print(f"[VoiceAssistant] TTS error: {e}")
        finally:
            self._done()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _set_state(self, state):
        GLib.idle_add(self.on_state_change, state)

    def _fail(self, msg):
        print(f"[VoiceAssistant] ERROR: {msg}")
        GLib.idle_add(self.on_error, msg)
        self._done()

    def _done(self):
        with self._lock:
            self._busy = False
        self._set_state("idle")
