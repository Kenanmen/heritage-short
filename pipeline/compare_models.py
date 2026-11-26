"""Experiment E01: same storyboard lines, same voices, different TTS models.
Writes outputs/experiments/e01_models/<model>/<shot>.wav and logs every call to runs.jsonl.
Usage: python pipeline/compare_models.py [--shots s02,s09] [--models a,b,c]
Only the model changes between runs, so differences you hear come from the model."""
from __future__ import annotations

import argparse
import os
import sys
import time

from common import OUT, call_with_retries, load_storyboard, wav_seconds
from narration import DEFAULT_MODELS, synth, write_wav


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shots", default="s02,s06,s09", help="comma-separated narrated shot ids")
    ap.add_argument("--models", default="", help="comma-separated model ids (default: GEMINI_TTS_MODEL or the built-in list)")
    a = ap.parse_args(argv)

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY is not set (put it in .env).")
        return 1
    sb = load_storyboard()
    models = [m.strip() for m in (a.models or os.environ.get("GEMINI_TTS_MODEL", "")).split(",") if m.strip()] or DEFAULT_MODELS
    wanted = [s.strip() for s in a.shots.split(",") if s.strip()]
    shots = {s["id"]: s for s in sb["shots"] if s["narration"]}
    missing = [w for w in wanted if w not in shots]
    if missing:
        print(f"not narrated shots: {missing}. Narrated shots are: {sorted(shots)}")
        return 1

    print(f"{'model':32} {'shot':5} {'result':8} {'latency_s':>9} {'audio_s':>7}")
    for model in models:
        d = OUT / "experiments" / "e01_models" / model
        d.mkdir(parents=True, exist_ok=True)
        for sid in wanted:
            n = shots[sid]["narration"]
            v = sb["voices"][n["speaker"]]
            params = {"experiment": "E01", "shot": sid, "voice": v["voice_name"], "style": v.get("style", ""),
                      "text_chars": len(n["text_am"]), "language": sb["language"]}
            t0 = time.time()
            try:
                pcm = call_with_retries("experiment_e01", model, params,
                                        lambda n=n, v=v, model=model: synth(n["text_am"], v["voice_name"], v.get("style", ""), model, key),
                                        attempts=2)
            except RuntimeError as e:
                print(f"{model:32} {sid:5} {'FAIL':8} {'-':>9} {'-':>7}  {str(e)[:100]}")
                continue
            path = d / f"{sid}.wav"
            write_wav(path, pcm)
            print(f"{model:32} {sid:5} {'ok':8} {time.time() - t0:9.1f} {wav_seconds(path):7.1f}")
    print(f"\nListen in: {OUT / 'experiments' / 'e01_models'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
