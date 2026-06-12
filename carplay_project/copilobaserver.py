import subprocess
import requests
from flask import Flask, request, Response

app = Flask(__name__)

# Local Ollama on your PC
OLLAMA_URL = "http://localhost:11434/api/generate"

PIPER_EXEC = "C:\\workspace\\piper\\piper.exe"
VOICE_MODEL = "C:\\workspace\\piper\\voicemodels\\es_AR-daniela-high.onnx"


def generate_audio_stream(prompt):
    """Generator that yields audio bytes as they are created."""
    print(f"Received prompt from car: {prompt}")

    # 1. Ask Ollama for the text response
    ollama_payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    # Make sure Ollama is running on Windows!
    ollama_res = requests.post(OLLAMA_URL, json=ollama_payload).json()
    response_text = ollama_res['response']
    print(f"Ollama generated: {response_text}")

    # 2. Run Piper directly (No shell=True, no 'echo')
    # We pass the arguments as a Python list. This is 100% safe on Windows.
    piper_cmd = [PIPER_EXEC, "--model", VOICE_MODEL, "--output_raw"]

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

@app.route('/ask', methods=['POST'])
def ask_copiloba():
    data = request.json
    prompt = data.get('prompt', '')

    if not prompt:
        return {"error": "No prompt provided"}, 400

    # Stream the audio response back to the board
    return Response(generate_audio_stream(prompt), mimetype="audio/raw")


if __name__ == '__main__':
    # Listen on all network interfaces (including Tailscale) on Port 5000
    app.run(host='0.0.0.0', port=5000)