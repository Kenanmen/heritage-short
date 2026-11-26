"""Stage: narration.
Reads storyboard.json, writes outputs/narration/<shot>.wav and outputs/narration/timing.json.
One Gemini TTS call per narrated shot. Each wav is cached by a hash of
(model, voice, style, spoken text, language), so editing one line regenerates only that line."""
from __future__ import annotations

import argparse
import base64
import os
import sys
import time
import wave
import json

import requests

from common import OUT, call_with_retries, input_hash, is_fresh, load_storyboard, repair_wrapped_wav, save_audio, wav_seconds, write_meta

# Model IDs: the brief names "Gemini 3.8 Flash TTS" but no API ID. The list below came from a cohort
# colleague. Set GEMINI_TTS_MODEL in .env (comma-separated) to the IDs smoke_test.py showed working.
DEFAULT_MODELS = ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-2.5-flash-preview-tts"]  # from Slack; UNVERIFIED: run smoke_test.py
SAMPLE_RATE = 24000  # Gemini TTS returns raw 16-bit mono PCM at 24 kHz (per the public API docs)


def synth(text: str, voice: str, style: str, model: str, key: str) -> bytes:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    prompt = f"{style}: {text}" if style else text
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    r = requests.post(url, headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=body, timeout=120)
    r.raise_for_status()
    data = r.json()
    cands = data.get("candidates") or []
    if not cands or "content" not in cands[0]:
        # Google replied 200 but without audio. Say why, so the failure can be diagnosed.
        reason = cands[0].get("finishReason") if cands else None
        raise RuntimeError(f"no audio in the reply: finishReason={reason}, promptFeedback={data.get('promptFeedback')}")
    part = cands[0]["content"]["parts"][0]
    return base64.b64decode(part["inlineData"]["data"])


def write_wav(path, data: bytes) -> None:
    save_audio(path, data, SAMPLE_RATE)


_last_call = [0.0]


def pace() -> None:
    """Free-tier Gemini TTS allows about 3 requests per minute (see the AI Studio rate-limit page),
    so keep at least TTS_MIN_INTERVAL_S seconds (default 21) between requests. Called BEFORE the logged call,
    so the latency in runs.jsonl is the API time only (runs before 26 Nov 17:50 UTC+3 logged wait + API time)."""
    gap = float(os.environ.get("TTS_MIN_INTERVAL_S", "21"))
    wait = _last_call[0] + gap - time.monotonic()
    if _last_call[0] and wait > 0:
        print(f"  pacing: waiting {wait:.0f}s to stay under the free-tier request rate")
        time.sleep(wait)
    _last_call[0] = time.monotonic()


def paced_synth(text, voice, style, model, key):
    return synth(text, voice, style, model, key)


def plan(sb: dict, model: str) -> list[dict]:
    items = []
    for shot in sb["shots"]:
        n = shot["narration"]
        if not n:
            continue
        v = sb["voices"][n["speaker"]]
        # The voice's "style" text is NOT sent: experiments E01/E02 showed the TTS models read it aloud
        # (a 2-word line became 3.9 s of audio instead of 1.1 s). Only the spoken text is sent.
        inputs = {"model": model, "voice": v["voice_name"], "style": "",
                  "text": n["text_am"], "language": sb["language"]}
        items.append({"id": shot["id"], "speaker": n["speaker"], "inputs": inputs, "hash": input_hash(inputs),
                      "wav": OUT / "narration" / f"{shot['id']}.wav", "status": n["text_status"]})
    return items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="regenerate only this shot id, e.g. s02")
    ap.add_argument("--dry-run", action="store_true", help="show what would be generated, call nothing")
    ap.add_argument("--force", action="store_true", help="ignore the cache for the selected shots")
    a = ap.parse_args(argv)

    sb = load_storyboard()
    models = [m.strip() for m in os.environ.get("GEMINI_TTS_MODEL", "").split(",") if m.strip()] or DEFAULT_MODELS
    model = models[0]  # preferred model; part of the cache key
    key = os.environ.get("GEMINI_API_KEY")
    items = [i for i in plan(sb, model) if not a.only or i["id"] == a.only]
    if a.only and not items:
        print(f"no narrated shot with id {a.only}")
        return 1
    (OUT / "narration").mkdir(parents=True, exist_ok=True)
    for i in items:  # early clips were saved with a double WAV header; repair them without any API call
        if i["wav"].exists() and repair_wrapped_wav(i["wav"]):
            print(f"{i['id']}: repaired an early clip (removed an extra WAV header)")

    todo = []
    for i in items:
        fresh = is_fresh(i["wav"], i["hash"]) and not a.force
        print(f"{i['id']} [{i['speaker']}] {'cached' if fresh else 'needs generation'}")
        if not fresh:
            todo.append(i)
    if any(i["status"] == "draft" for i in items):
        print("Note: some spoken text is still 'draft'. Have a native speaker listen before relying on it.")
    if a.dry_run:
        return 0
    if todo and not key:
        print("GEMINI_API_KEY is not set (put it in .env). Nothing generated.")
        return 1

    for i in todo:
        inp = i["inputs"]
        params = {"voice": inp["voice"], "style": inp["style"], "text_chars": len(inp["text"]), "language": inp["language"]}
        pcm, used = None, None
        for m in models:  # fall back to the next model when one is unavailable or over quota
            try:
                pace()
                pcm = call_with_retries("narration", m, params,
                                        lambda inp=inp, m=m: paced_synth(inp["text"], inp["voice"], inp["style"], m, key), attempts=3)
                used = m
                break
            except RuntimeError as e:
                print(f"{i['id']}: {m} failed ({str(e)[:120]}); trying next model")
        if pcm is None:
            print(f"{i['id']}: every model failed")
            return 1
        write_wav(i["wav"], pcm)
        secs = wav_seconds(i["wav"])
        write_meta(i["wav"], i["hash"], model=used, voice=inp["voice"], seconds=round(secs, 3))
        print(f"{i['id']} generated, {secs:.1f}s")

    timing = {s["id"]: round(wav_seconds(OUT / "narration" / f"{s['id']}.wav"), 3)
              for s in sb["shots"] if s["narration"] and (OUT / "narration" / f"{s['id']}.wav").exists()}
    (OUT / "narration" / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
