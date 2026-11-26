#!/usr/bin/env python3
"""One command for the whole pipeline.

    python film.py                      validate -> narration -> radio cut (the stages that exist so far)
    python film.py narration --only s02 regenerate the narration of one shot (cache skips the rest)
    python film.py validate | narration | radio

Keyframes, moving shots, music and the final edit are added here as they are built."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGES = {
    "validate": ["pipeline/validate.py"],
    "narration": ["pipeline/narration.py"],
    "radio": ["pipeline/assemble.py", "radio"],
}
ORDER = ["validate", "narration", "radio"]


def run(stage: str, extra: list) -> None:
    print(f"\n=== {stage} ===", flush=True)
    r = subprocess.run([sys.executable, *STAGES[stage], *extra], cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"stage '{stage}' failed (exit {r.returncode})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", nargs="?", default="all", choices=["all", *ORDER])
    args, extra = ap.parse_known_args()
    if args.stage == "all":
        for s in ORDER:
            run(s, [])
    else:
        if args.stage != "validate":
            run("validate", [])
        run(args.stage, extra)


if __name__ == "__main__":
    main()
