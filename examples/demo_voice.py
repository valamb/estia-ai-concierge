"""
Voice Interaction Demo
======================
Demonstrates the ESTIA voice round-trip:

1. Record or load a WAV file
2. POST to /api/v1/voice/chat
3. Receive a text reply and save the MP3 audio response

Usage:
    python examples/demo_voice.py --audio path/to/question.wav

Requirements:
    - ESTIA server running:  uvicorn app.main:app --reload
    - OPENAI_API_KEY set in .env
"""

import argparse
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)


BASE_URL = "http://localhost:8000/api/v1"


def demo_voice_chat(audio_path: Path, save_audio: bool = True) -> None:
    print(f"\n ESTIA Voice Demo")
    print(f" Audio file: {audio_path}\n")

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{BASE_URL}/voice/chat",
            files={"audio": (audio_path.name, audio_bytes, "audio/wav")},
            data={"tts_enabled": "true"},
        )

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return

    data = response.json()
    print(f"You said   : {data['transcript']}")
    print(f"Language   : {data['language_detected']}")
    print(f"ESTIA says : {data['reply']}")
    print(f"Tokens used: {data['tokens_used']}")

    if data["audio_available"] and save_audio:
        # Fetch the MP3 via the /speak endpoint using the reply text
        speak_response = httpx.post(
            f"{BASE_URL}/voice/speak",
            data={"text": data["reply"], "language": data["language_detected"]},
            timeout=30,
        )
        if speak_response.status_code == 200:
            out_path = Path("estia_reply.mp3")
            out_path.write_bytes(speak_response.content)
            print(f"\n Audio saved to: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ESTIA Voice Demo")
    parser.add_argument("--audio", required=True, help="Path to WAV audio file")
    parser.add_argument("--no-audio", action="store_true", help="Skip saving MP3")
    args = parser.parse_args()

    audio_file = Path(args.audio)
    if not audio_file.exists():
        print(f"File not found: {audio_file}")
        sys.exit(1)

    demo_voice_chat(audio_path=audio_file, save_audio=not args.no_audio)
