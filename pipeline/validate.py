"""Validate storyboard.json against schema/storyboard.schema.json and print a summary.
Every other stage calls the same check through common.load_storyboard()."""
from __future__ import annotations

import json
import sys

from common import STORYBOARD, nominal_total, validation_errors


def main() -> int:
    sb = json.loads(STORYBOARD.read_text(encoding="utf-8"))
    errs = validation_errors(sb)
    if errs:
        print("INVALID storyboard:")
        for e in errs:
            print(" -", e)
        return 1
    print(f"OK  {sb['title']}  ({len(sb['shots'])} shots, nominal {nominal_total(sb):.0f}s incl. {sb['end_card']['duration_s']}s end card)")
    print(f"{'id':4} {'size':13} {'cam':9} {'sec':>4}  narration")
    drafts = 0
    for s in sb["shots"]:
        n = s["narration"]
        who = f"{n['speaker']} ({len(n['text_en'].split())} words en)" if n else "-"
        drafts += bool(n and n["text_status"] == "draft")
        print(f"{s['id']:4} {s['size']:13} {s['camera']:9} {s['duration_s']:>4}  {who}")
    if drafts:
        print(f"\nNote: {drafts} narration line(s) are still 'draft' (not proofread by a native speaker).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
