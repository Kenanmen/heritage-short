#!/usr/bin/env python3
"""Keyframe experiments E04-E07 on one shot (s06), one factor changed per experiment, seed fixed.
    python pipeline/compare_keyframes.py        (8 FLUX calls, a few seconds each; every call is logged)
Results go to outputs/experiments/e0X_*/ ; the judgement is the author's, written in EXPERIMENTS.md."""
import base64
import os
import sys

import requests

from common import OUT, call_with_retries, load_storyboard

sb = load_storyboard()
shot = next(s for s in sb["shots"] if s["id"] == "s06")
base = shot["image_prompt"]
style, neg, seed = sb["style_block"], sb["negative_style"], shot["seed"]
full = f"{base} {style} Avoid: {neg}."
EXPS = {  # id: (variant name -> (prompt, steps, seed)), A is the control
    "e04_style_block": {"A_with_style": (full, 6, seed), "B_no_style": (base, 6, seed)},
    "e05_steps": {"A_steps6": (full, 6, seed), "B_steps8": (full, 8, seed)},
    "e06_seed": {"A_seed": (full, 6, seed), "B_seed_plus1": (full, 6, seed + 1)},
    "e07_negative": {"A_with_avoid": (full, 6, seed), "B_no_avoid": (f"{base} {style}", 6, seed)},
}
acct, tok = os.environ.get("CF_ACCOUNT_ID"), os.environ.get("CF_API_TOKEN")
model = os.environ.get("CF_IMAGE_MODEL") or "@cf/black-forest-labs/flux-1-schnell"
if not (acct and tok):
    sys.exit("CF_ACCOUNT_ID / CF_API_TOKEN missing in .env")
url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{model}"
for exp, variants in EXPS.items():
    d = OUT / "experiments" / exp
    d.mkdir(parents=True, exist_ok=True)
    for name, (prompt, steps, sd) in variants.items():
        def call():
            r = requests.post(url, headers={"Authorization": f"Bearer {tok}"}, timeout=120,
                              json={"prompt": prompt, "steps": steps, "seed": sd})
            r.raise_for_status()
            return r.json()["result"]["image"]
        b64 = call_with_retries(f"experiment_{exp[:3]}", model, {"experiment": exp[:3], "variant": name, "steps": steps}, call, seed=sd)
        (d / f"{name}.jpg").write_bytes(base64.b64decode(b64))
        print(exp, name, "saved")
