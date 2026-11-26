"""Smoke test: one real call to each provider, latency logged to runs.jsonl.
Run this first. For Gemini it tries each candidate TTS model once and saves an Amharic clip per
model, so you can hear the greeting before anything else depends on it."""
from __future__ import annotations

import base64
import os
import sys
import wave

import requests

from common import OUT, call_with_retries, save_audio

# Model IDs suggested by a cohort colleague on Slack. UNVERIFIED: this test finds out which work.
# Override with GEMINI_TTS_MODEL in .env (comma-separated list, tried in order).
CANDIDATE_MODELS = ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-2.5-flash-preview-tts"]
VOICE = "Sulafat"  # UNVERIFIED voice name: change it if the API rejects it
STYLE = "Say warmly and calmly"
PROBES = {"greeting": "እንኳን አደረሳችሁ", "jebena": "ጀበና"}
SAMPLE_RATE = 24000  # raw 16-bit mono PCM at 24 kHz, per the public Gemini TTS docs


def tts(text: str, model: str, key: str) -> bytes:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": f"{STYLE}: {text}"}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}},
        },
    }
    r = requests.post(url, headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=body, timeout=120)
    r.raise_for_status()
    part = r.json()["candidates"][0]["content"]["parts"][0]
    return base64.b64decode(part["inlineData"]["data"])


def save_wav(path, data: bytes) -> None:
    save_audio(path, data, SAMPLE_RATE)


def gemini() -> list[tuple[str, str, str]]:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return [("SKIP", "Gemini TTS", "GEMINI_API_KEY not set")]
    models = [m.strip() for m in os.environ.get("GEMINI_TTS_MODEL", "").split(",") if m.strip()] or CANDIDATE_MODELS
    d = OUT / "smoke"
    d.mkdir(parents=True, exist_ok=True)
    rows, working = [], None
    for model in models:
        try:
            pcm = call_with_retries("smoke_tts", model, {"voice": VOICE, "probe": "greeting"},
                                    lambda m=model: tts(PROBES["greeting"], m, key), attempts=2)
        except RuntimeError as e:
            rows.append(("FAIL", f"Gemini TTS {model}", str(e)[:300]))
            continue
        save_wav(d / f"greeting_{model}.wav", pcm)
        rows.append(("PASS", f"Gemini TTS {model}", f"saved {d}/greeting_{model}.wav"))
        working = working or model
    if working:
        try:
            pcm = call_with_retries("smoke_tts", working, {"voice": VOICE, "probe": "jebena"},
                                    lambda: tts(PROBES["jebena"], working, key), attempts=2)
            save_wav(d / f"jebena_{working}.wav", pcm)
            rows.append(("PASS", f"Gemini TTS {working}", f"saved {d}/jebena_{working}.wav"))
        except RuntimeError as e:
            rows.append(("FAIL", f"Gemini TTS {working} (jebena)", str(e)[:300]))
    return rows


def cloudflare() -> list[tuple[str, str, str]]:
    acct, tok = os.environ.get("CF_ACCOUNT_ID"), os.environ.get("CF_API_TOKEN")
    if not (acct and tok):
        return [("SKIP", "Cloudflare image", "CF_ACCOUNT_ID / CF_API_TOKEN not set")]
    model = os.environ.get("CF_IMAGE_MODEL") or "@cf/black-forest-labs/flux-1-schnell"  # UNVERIFIED default
    url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{model}"

    def call() -> str:
        r = requests.post(url, headers={"Authorization": f"Bearer {tok}"}, timeout=120,
                          json={"prompt": "warm hand-painted illustration of a clay pan with round loaves over embers", "steps": 4})
        r.raise_for_status()
        return r.json()["result"]["image"]

    try:
        b64 = call_with_retries("smoke_image", model, {"steps": 4}, call, attempts=2)
    except RuntimeError as e:
        return [("FAIL", f"Cloudflare {model}", str(e)[:300])]
    d = OUT / "smoke"
    d.mkdir(parents=True, exist_ok=True)
    (d / "image_probe.jpg").write_bytes(base64.b64decode(b64))
    return [("PASS", f"Cloudflare {model}", f"saved {d}/image_probe.jpg")]


def main() -> int:
    # Gemini TTS has a tiny free daily quota (10 requests per model), so it is only tested on request.
    # Usage: python pipeline/smoke_test.py            -> Cloudflare only
    #        python pipeline/smoke_test.py --gemini   -> also spend Gemini TTS requests
    rows = (gemini() if "--gemini" in sys.argv else [("SKIP", "Gemini TTS", "not run (use --gemini; it spends free-tier quota)")]) + cloudflare()
    for status, name, note in rows:
        print(f"{status:5} {name}: {note}")
    print("Kaggle / Colab GPU: check by hand (phone verified, GPU switch available, weekly quota visible).")
    print("Latency per call is in runs.jsonl.")
    return 1 if any(r[0] == "FAIL" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
