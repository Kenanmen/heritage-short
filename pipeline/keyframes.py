#!/usr/bin/env python3
"""Keyframe stage: one still per shot from Cloudflare Workers AI (FLUX), cropped to 16:9 and 9:16.

    python pipeline/keyframes.py                 all shots (cache skips unchanged prompts)
    python pipeline/keyframes.py --only s06      regenerate one shot only (the walkthrough demo)
    python pipeline/keyframes.py --dry-run       print prompts, spend nothing

Prompt = shot.image_prompt + storyboard.style_block (+ 'Avoid:' negative_style).
Cache key = hash(model, prompt, steps). No seed: Cloudflare flux-1-schnell rejects one (HTTP 400), so re-running a changed prompt gives a new random draw; the cache is what keeps unchanged shots stable. Change one prompt -> only that shot regenerates."""
import argparse
import base64
import os
import subprocess
import sys

import requests

from common import OUT, call_with_retries, input_hash, is_fresh, load_storyboard, write_meta

STEPS = 6  # flux-1-schnell allows up to 8


def build_prompt(sb: dict, shot: dict) -> str:
    return f"{shot['image_prompt']} {sb['style_block']} Avoid: {sb['negative_style']}."


def crop(src, dst_wide, dst_tall) -> None:
    for dst, vf in ((dst_wide, "crop=iw:iw*9/16"), (dst_tall, "crop=ih*9/16:ih")):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf", vf, "-q:v", "2", str(dst)], check=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    sb = load_storyboard()
    model = os.environ.get("CF_IMAGE_MODEL") or "@cf/black-forest-labs/flux-1-schnell"
    acct, tok = os.environ.get("CF_ACCOUNT_ID"), os.environ.get("CF_API_TOKEN")
    d = OUT / "keyframes"
    d.mkdir(parents=True, exist_ok=True)
    for shot in sb["shots"]:
        sid = shot["id"]
        if a.only and sid != a.only:
            continue
        prompt = build_prompt(sb, shot)
        inputs = {"model": model, "prompt": prompt, "steps": STEPS}  # schnell on Cloudflare rejects a seed input
        h = input_hash(inputs)
        raw = d / f"{sid}.jpg"
        if is_fresh(raw, h) and not a.force:
            print(f"{sid}: cached")
            continue
        if a.dry_run:
            print(f"{sid}: would generate | {prompt[:110]}...")
            continue
        if not (acct and tok):
            sys.exit("CF_ACCOUNT_ID / CF_API_TOKEN missing in .env")
        url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{model}"

        def call():
            r = requests.post(url, headers={"Authorization": f"Bearer {tok}"}, timeout=120,
                              json={"prompt": prompt, "steps": STEPS})
            r.raise_for_status()
            return r.json()["result"]["image"]

        b64 = call_with_retries("keyframe", model, {"shot": sid, "steps": STEPS}, call)
        raw.write_bytes(base64.b64decode(b64))
        crop(raw, d / f"{sid}_16x9.jpg", d / f"{sid}_9x16.jpg")
        write_meta(raw, h, model=model)
        print(f"{sid}: generated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
