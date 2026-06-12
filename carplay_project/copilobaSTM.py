import requests
import json
import subprocess

# Pointing to the new Flask Server on Port 5000
FLASK_SERVER_IP = "100.109.4.120"
FLASK_URL = f"http://{FLASK_SERVER_IP}:5000/ask"


def ask_copiloba_voice(user_prompt):
    print(f"Sending audio transcription to Power PC: '{user_prompt}'")

    payload = {
        "prompt": f"Eres Copiloba, una asistente muy loba dentro de un vehiculo embebido. Se breve, el conductor dice: {user_prompt}"
    }

    try:
        # Notice stream=True! This is critical so we play audio while it downloads
        response = requests.post(FLASK_URL, json=payload, stream=True, timeout=20)
        response.raise_for_status()

        print("Receiving audio from PC... Playing now!")

        # Open ALSA playback pipe on the board
        # ⚠️ CRITICAL: Match the '-r' (sample rate) to your Piper model on the PC!
        # Low quality models usually use 16000, medium/high use 22050.
        player = subprocess.Popen(
            ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-'],
            stdin=subprocess.PIPE
        )

        # Write the incoming internet bytes directly to the speakers
        for chunk in response.iter_content(chunk_size=4096):
            if chunk:
                player.stdin.write(chunk)

        # Close the player when the stream finishes
        player.stdin.close()
        player.wait()

        print("Finished speaking.")

    except requests.exceptions.RequestException as e:
        print(f"Failed to reach Power PC! Error: {e}")
    except Exception as e:
        print(f"Audio playback error: {e}")


# --- Test the System ---
if __name__ == "__main__":
    ask_copiloba_voice("Prende el spotify y el aire acondicionado.")