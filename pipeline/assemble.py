"""Stage: assemble (FFmpeg only, no model calls).
`radio` builds the radio cut: narration over placeholder music on a black screen, with the music
ducked under the voice and the mix normalised to about -14 LUFS. Later subcommands (rough, final)
will be added here and read the same storyboard."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time

from common import OUT, effective_duration, load_storyboard, log_call, narration_lengths


def run(cmd: list) -> None:
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("ffmpeg failed:\n" + " ".join(str(c) for c in cmd) + "\n" + p.stderr[-1500:])


def radio() -> int:
    ff = shutil.which("ffmpeg")
    if not ff:
        print("ffmpeg not found on PATH.")
        return 1
    t0 = time.time()
    sb = load_storyboard()
    lengths = narration_lengths()
    nar_dir = OUT / "narration"
    tmp = OUT / "radio_tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    print(f"{'id':4} {'planned':>8} {'voice':>7} {'used':>7}")
    segs, total, missing = [], 0.0, 0
    for s in sb["shots"]:
        n, wav = s["narration"], nar_dir / f"{s['id']}.wav"
        d = effective_duration(s, lengths)
        seg = tmp / f"{s['id']}.wav"
        if n and wav.exists():
            delay_ms = int(n.get("delay_s", 0.5) * 1000)
            run([ff, "-y", "-i", wav, "-af", f"aresample=48000,adelay={delay_ms}:all=1,apad=whole_dur={d:.3f}",
                 "-ac", 1, "-t", f"{d:.3f}", seg])
        else:
            missing += bool(n)
            run([ff, "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{d:.3f}", seg])
        voice = lengths.get(s["id"])
        flag = "  <- narration longer than planned shot" if d > s["duration_s"] + 1e-6 else ""
        print(f"{s['id']:4} {s['duration_s']:>7}s {('%.1fs' % voice) if voice else '-':>7} {d:>6.1f}s{flag}")
        segs.append(seg)
        total += d
    if missing:
        print(f"Warning: {missing} narrated shot(s) have no audio yet (silence used). Run the narration stage first.")

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segs), encoding="utf-8")
    narr = tmp / "narration_all.wav"
    run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", narr])

    # Placeholder score: three quiet sine tones with a slow tremolo. Replaced by ACE-Step in phase 2.
    music = tmp / "placeholder_music.wav"
    tone = lambda f: ["-f", "lavfi", "-i", f"sine=frequency={f}:sample_rate=48000:duration={total:.3f}"]
    run([ff, "-y", *tone(110), *tone(165), *tone(220), "-filter_complex",
         f"[0:a][1:a][2:a]amix=inputs=3:normalize=0,volume=0.12,tremolo=f=0.25:d=0.5,"
         f"afade=t=in:d=2,afade=t=out:st={max(total - 2, 0):.3f}:d=2,aformat=channel_layouts=mono[m]",
         "-map", "[m]", music])

    # Ducking uses the starting values from the brief: threshold 0.02, ratio 6, attack 300 ms, release 1500 ms.
    out = OUT / "radio_cut.mp4"
    run([ff, "-y", "-i", music, "-i", narr, "-f", "lavfi", "-i", "color=c=black:s=360x640:r=24",
         "-filter_complex",
         "[1:a]asplit=2[v1][v2];"
         "[0:a][v2]sidechaincompress=threshold=0.02:ratio=6:attack=300:release=1500[duck];"
         "[duck][v1]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1:LRA=11,aresample=48000[a]",
         "-map", "2:v", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out])

    latency = round(time.time() - t0, 2)
    log_call(stage="assemble_radio", model="ffmpeg", params={"total_s": round(total, 2), "shots": len(segs)},
             seed=None, latency_s=latency, cost_usd=0.0, status="ok")
    print(f"\nRadio cut: {out}  ({total:.1f}s, built in {latency}s)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["radio"])
    a = ap.parse_args(argv)
    return radio() if a.cmd == "radio" else 1


if __name__ == "__main__":
    sys.exit(main())
