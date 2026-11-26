#!/usr/bin/env python3
"""Experiment E09: two ducking settings under the same narration, by ear (FFmpeg only, no model call, no quota).
A = threshold 0.02, ratio 6, attack 300 ms, release 1500 ms (our starting values)
B = threshold 0.02, ratio 3, attack 100 ms, release 600 ms (lighter and faster)
Output: outputs/experiments/e09_ducking/A.mp3, B.mp3 (first ~13 s: s01 + s02 narration over the score)."""
import shutil
import subprocess
import sys
import time

from common import OUT, log_call

ff = shutil.which("ffmpeg")
nar, music = OUT / "narration", OUT / "music" / "main.wav"
if not (ff and (nar / "s01.wav").exists() and music.exists()):
    sys.exit("Need ffmpeg, outputs/narration/s01.wav and s02.wav, and outputs/music/main.wav (run: python film.py music)")
d = OUT / "experiments" / "e09_ducking"
d.mkdir(parents=True, exist_ok=True)
for name, ratio, att, rel in (("A", 6, 300, 1500), ("B", 3, 100, 600)):
    t0 = time.time()
    fc = ("[1:a]aresample=48000,adelay=500:all=1[n1];[2:a]aresample=48000,adelay=6500:all=1[n2];[n1][n2]amix=inputs=2:normalize=0,apad=whole_dur=13[v];"
          "[v]asplit=2[v1][v2];[0:a]aresample=48000,volume=0.9[m];"
          f"[m][v2]sidechaincompress=threshold=0.02:ratio={ratio}:attack={att}:release={rel}[duck];[duck][v1]amix=inputs=2:normalize=0[o]")
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(music), "-i", str(nar / "s01.wav"), "-i", str(nar / "s02.wav"),
                    "-filter_complex", fc, "-map", "[o]", "-t", "13", "-b:a", "128k", str(d / f"{name}.mp3")], check=True)
    log_call(stage="experiment_E09", model="ffmpeg", params={"variant": name, "ratio": ratio, "attack_ms": att, "release_ms": rel},
             seed=None, latency_s=round(time.time() - t0, 2), cost_usd=0.0, status="ok")
    print(name, "saved")
