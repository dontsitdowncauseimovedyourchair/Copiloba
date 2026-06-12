import os
import requests
import subprocess

# Replace with your PC's IP or Tailscale IP
SERVER_URL = "http://100.109.4.120:5000/ask_audio"
AUDIO_FILE = "/tmp/driver_voice.wav"


def listen_and_ask():
    print("🎤 Escuchando... (Speak now for 4 seconds)")

    # 1. Record 4 seconds of audio natively via ALSA (Zero Yocto required!)
    # Change hw:1,0 to match your Logitech mic from 'arecord -l'

    os.system(f"arecord -D plughw:1,0 -c 2 -d 6 -f S16_LE -r 16000 {AUDIO_FILE}")
    print("📡 Enviando a Copiloba...")

    # 2. Send the .wav file to your PC Server
    with open(AUDIO_FILE, 'rb') as f:
        files = {'audio': ('driver_voice.wav', f, 'audio/wav')}
        try:
            response = requests.post(SERVER_URL, files=files, stream=True)

            if response.status_code == 200:
                print("🔊 Copiloba está hablando...")

                # 3. Pipe the incoming audio stream directly to the speakers!
                # Ensure the ALSA format matches Piper's output (22050Hz, S16_LE, Mono)
                play_process = subprocess.Popen(
                    ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-c', '1'],
                    stdin=subprocess.PIPE
                )

                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        play_process.stdin.write(chunk)

                play_process.stdin.close()
                play_process.wait()
            else:
                print(f"Error del servidor: {response.text}")

        except Exception as e:
            print(f"Error de conexión: {e}")


if __name__ == "__main__":
    # In your final GTK app, trigger this function when a steering wheel button is pressed!
    listen_and_ask()
