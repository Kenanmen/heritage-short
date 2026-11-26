"""List the Gemini models whose names mention TTS, so the exact model IDs are known, not guessed.
Listing models does not use generation quota. Usage: python pipeline/list_models.py"""
from __future__ import annotations

import os
import sys

import requests

import common  # noqa: F401  (loads .env)


def main() -> int:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY is not set (put it in .env).")
        return 1
    url, token, found = "https://generativelanguage.googleapis.com/v1beta/models", None, []
    while True:
        r = requests.get(url, headers={"x-goog-api-key": key}, params={"pageSize": 200, **({"pageToken": token} if token else {})}, timeout=60)
        r.raise_for_status()
        data = r.json()
        found += data.get("models", [])
        token = data.get("nextPageToken")
        if not token:
            break
    tts = [m for m in found if "tts" in m["name"].lower()]
    print(f"{len(found)} models visible to this key; {len(tts)} mention TTS:")
    for m in tts:
        print(f"  {m['name'].removeprefix('models/'):45} {','.join(m.get('supportedGenerationMethods', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
