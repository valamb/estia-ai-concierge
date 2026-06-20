"""
Image Recognition Demo
======================
Demonstrates ESTIA's GPT-4o Vision capability:

1. Upload an image file (JPEG, PNG)
2. Ask a question about it
3. Receive a hotel-concierge-context reply

Usage:
    python examples/demo_image.py --image path/to/photo.jpg
    python examples/demo_image.py --image pool.jpg --question "What pool is this?"
    python examples/demo_image.py --image dish.jpg --question "What dish is this and can I order it?" --lang el

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

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def demo_image_chat(
    image_path: Path,
    question: str,
    language: str | None = None,
    property_id: str | None = None,
) -> None:
    content_type = MIME_TYPES.get(image_path.suffix.lower(), "image/jpeg")

    print(f"\n ESTIA Image Demo")
    print(f" Image   : {image_path}")
    print(f" Question: {question}\n")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    form_data: dict = {"question": question}
    if language:
        form_data["language"] = language
    if property_id:
        form_data["property_id"] = property_id

    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{BASE_URL}/image/chat",
            files={"image": (image_path.name, image_bytes, content_type)},
            data=form_data,
        )

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return

    data = response.json()
    print(f"Language       : {data['language_detected']}")
    print(f"Tokens used    : {data['tokens_used']}")
    print(f"\nESTIA says:\n{data['reply']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ESTIA Image Demo")
    parser.add_argument("--image", required=True, help="Path to image file")
    parser.add_argument(
        "--question",
        default="What can you tell me about this?",
        help="Question about the image",
    )
    parser.add_argument("--lang", help="Language: en or el")
    parser.add_argument("--property", help="Property ID (e.g. porto_elounda)")
    args = parser.parse_args()

    path = Path(args.image)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    demo_image_chat(
        image_path=path,
        question=args.question,
        language=args.lang,
        property_id=args.property,
    )
