#!/usr/bin/env python3
"""Music stage: our own synthesised score (no third-party audio, no model call, no quota).

Follows the storyboard cue 'main' (76 bpm; soft plucked strings, light hand drum, no strong lead, leaves room for voice):
 - (disabled, PLUCKS=False) plucked lyre-like notes (Karplus-Strong, krar-like) on a pentatonic scale in the tizita/ambassel family (A C D E G is the plain
   minor pentatonic; we use A B C E F, 'tizita minor'), sparse and mostly stepwise, with rests;
 - a soft kebero-like hand drum: low thump on beats 1 and 3, small slap on beat 4;
 - a breathy washint-like (bamboo flute) note every ~6-10 beats;
 - a quiet low drone (A2 + E3).
These EVOKE krar, kebero and washint; they are not recordings or authentic instrument models.
Deterministic: fixed random seed 76, so the same file comes out every run. Output: outputs/music/main.wav (48 kHz mono 16-bit).
    python pipeline/music.py [--seconds 70]"""
import argparse
import math
import random
import struct
import sys
import time
import wave

from common import OUT, load_storyboard, log_call

SR = 48000


def pluck(freq: float, dur: float, rnd: random.Random, decay: float = 0.996) -> list:
    n = int(SR / freq)
    buf = [rnd.uniform(-1, 1) for _ in range(n)]
    out, prev = [], 0.0
    for i in range(int(dur * SR)):
        j = i % n
        v = 0.5 * (buf[j] + buf[(j + 1) % n]) * decay
        buf[j] = v
        prev = prev + 0.35 * (v - prev)  # gentle low-pass: rounder, less metallic
        out.append(prev)
    fade = int(0.05 * SR)
    for i in range(fade):
        out[-1 - i] *= i / fade
    return out


def washint(freq: float, dur: float, rnd: random.Random) -> list:
    """Breathy bamboo-flute-like tone: sine + a little 2nd harmonic, slow vibrato, low-passed breath noise."""
    n, out, br = int(dur * SR), [], 0.0
    for i in range(n):
        x = i / SR
        vib = 1 + 0.006 * math.sin(2 * math.pi * 5.0 * x)
        env = min(1.0, x / 0.15) * min(1.0, (dur - x) / 0.35) * (0.85 + 0.15 * math.sin(2 * math.pi * 0.9 * x))
        br += 0.15 * (rnd.uniform(-1, 1) - br)
        out.append(env * (math.sin(2 * math.pi * freq * vib * x) + 0.18 * math.sin(4 * math.pi * freq * vib * x) + 0.35 * br))
    return out


def add(mix, samples, start, gain) -> None:
    s0 = int(start * SR)
    for i, v in enumerate(samples):
        if s0 + i >= len(mix):
            break
        mix[s0 + i] += v * gain


PLUCKS = False  # krar-like plucks removed by the author (did not sound right); flute, drum and drone remain


def build(seconds: float, bpm: float = 76.0, seed: int = 76) -> list:
    rnd = random.Random(seed)
    mix = [0.0] * int(seconds * SR)
    beat = 60.0 / bpm
    A3 = 220.0
    ratios = [1, 9 / 8, 6 / 5, 3 / 2, 8 / 5]  # A B C E F relative to A (just intonation, approx.)
    scale = [A3 * r for r in ratios] + [A3 * 2 * r for r in ratios[:3]]
    idx, t, bar = 2, beat * 2, 0
    while PLUCKS and t < seconds - 3:
        if rnd.random() < 0.62:  # sparse: ~38% rests
            idx = max(0, min(len(scale) - 1, idx + rnd.choice([-2, -1, -1, 0, 1, 1, 2])))
            f = scale[idx]
            add(mix, pluck(f, 1.6, rnd), t, 0.22)
            if rnd.random() < 0.18:  # occasional soft fifth below
                add(mix, pluck(f * 2 / 3, 1.6, rnd), t, 0.10)
        t += beat / 2 * rnd.choice([1, 1, 2])
    # washint: a sparse long note about every 12 beats, starting after the opening
    tf, hi = beat * 6, [A3 * 2 * r for r in ratios] + [A3 * 4 * ratios[0]]
    while tf < seconds - 6:
        add(mix, washint(rnd.choice(hi), rnd.choice([2.2, 2.8, 3.4]), rnd), tf, 0.16)
        tf += beat * rnd.choice([6, 8, 10])
    # soft hand drum (kebero-like): low thump on beats 1 and 3, a higher slap on beat 4
    k, tb = 0, 0.0
    while tb < seconds - 2:
        if k % 4 in (0, 2):
            n = int(0.28 * SR)
            thump = [math.sin(2 * math.pi * (62 + 38 * math.exp(-i / (0.03 * SR))) * i / SR) * math.exp(-i / (0.07 * SR)) for i in range(n)]
            add(mix, thump, tb, 0.20 if k % 4 == 0 else 0.12)
        if k % 4 == 3:
            n = int(0.12 * SR)
            slap = [(rnd.uniform(-1, 1) * 0.5 + math.sin(2 * math.pi * 210 * i / SR)) * math.exp(-i / (0.025 * SR)) for i in range(n)]
            add(mix, slap, tb, 0.07)
        k += 1
        tb += beat
    # drone
    for i in range(len(mix)):
        x = i / SR
        mix[i] += 0.05 * math.sin(2 * math.pi * 110 * x) + 0.03 * math.sin(2 * math.pi * 164.8 * x)
    peak = max(abs(v) for v in mix) or 1.0
    k = 0.45 / peak  # peak about -7 dBFS; loudness is set later by loudnorm
    return [v * k for v in mix]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    sb = load_storyboard()
    seconds = a.seconds or 80.0  # longer than the film; the final stage trims and fades
    cue = sb["music"]["cues"][0]
    t0 = time.time()
    samples = build(seconds, bpm=float(cue["bpm"]))
    dst = OUT / "music" / "main.wav" if not a.out else __import__("pathlib").Path(a.out)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in samples))
    lat = round(time.time() - t0, 2)
    log_call(stage="music", model="own_synthesis(pipeline/music.py)", params={"bpm": cue["bpm"], "seconds": seconds, "seed": 76},
             seed=76, latency_s=lat, cost_usd=0.0, status="ok")
    print(f"Score written: {dst}  ({seconds:.0f}s, {lat}s to synthesise)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
