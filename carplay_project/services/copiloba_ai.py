# services/copiloba_ai.py
import os
import json      # NUEVO
import base64    # NUEVO
import requests
import subprocess
import threading
from gi.repository import GLib

SERVER_URL = "http://100.109.4.120:5000/ask_audio"
AUDIO_FILE = "/tmp/driver_voice.wav"


class CopilobaAssistant:
    def __init__(self, status_callback=None, command_callback=None):   # NUEVO param
        # This callback allows the AI to send text updates back to the GTK screen
        self.status_callback = status_callback
        self.command_callback = command_callback                       # NUEVO

    def _update_ui(self, message):
        # Safely push updates to the GTK main loop without crashing it
        if self.status_callback:
            GLib.idle_add(self.status_callback, message)

    def _listen_and_ask_worker(self):
        """This runs in the background so the dashboard doesn't freeze."""
        self._update_ui("Háblale a Copiloba... (6s)")

        # 1. Record audio
        os.system(f"arecord -D plughw:1,0 -c 2 -d 6 -f S16_LE -r 16000 {AUDIO_FILE}")
        self._update_ui("Pensando Lobamente...")

        # 2. Send to Server
        try:
            with open(AUDIO_FILE, 'rb') as f:
                files = {'audio': ('driver_voice.wav', f, 'audio/wav')}
                response = requests.post(SERVER_URL, files=files, stream=True)

                if response.status_code == 200:
                    self._update_ui("Loba Loba")

                    # NUEVO: ejecutar el comando ANTES de reproducir el audio,
                    # así el volumen/canción/ruta cambia mientras Copiloba habla
                    cmd_b64 = response.headers.get("X-Copiloba-Action")
                    if cmd_b64 and self.command_callback:
                        try:
                            cmd = json.loads(base64.b64decode(cmd_b64).decode("utf-8"))
                            self.command_callback(cmd)
                        except Exception as e:
                            print(f"Action parse error: {e}")

                    # 3. Play audio
                    play_process = subprocess.Popen(
                        ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-c', '1'],
                        stdin=subprocess.PIPE
                    )

                    for chunk in response.iter_content(chunk_size=4096):
                        if chunk:
                            play_process.stdin.write(chunk)

                    play_process.stdin.close()
                    play_process.wait()

                    self._update_ui("")  # Reset UI when done
                else:
                    self._update_ui(f"Flop del servidor: {response.status_code}")

        except Exception as e:
            self._update_ui("Flop de conexión a copiloba")
            print(f"Connection Error: {e}")

    def trigger_assistant(self):
        """This is the function main.py will call when a button is pressed."""
        # Launch the worker in a background thread instantly
        thread = threading.Thread(target=self._listen_and_ask_worker, daemon=True)
        thread.start()