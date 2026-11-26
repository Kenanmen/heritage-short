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


FPS = 24
SIZES = {"16x9": (1280, 720), "9x16": (720, 1280)}


def camera_filter(cam: str, n: int, w: int, h: int) -> str:
    """Ken Burns move on a still. Zoom 1.0 -> 1.18 (push_in), 1.18 -> 1.0 (pull_out), pans at 1.15."""
    c = "iw/2-(iw/zoom/2)"
    cy = "ih/2-(ih/zoom/2)"
    z, x, y = "1.0", c, cy
    if cam == "push_in":
        z = f"1+0.18*on/{n}"
    elif cam == "pull_out":
        z = f"1.18-0.18*on/{n}"
    elif cam == "pan_right":
        z, x = "1.15", f"(iw-iw/zoom)*on/{n}"
    elif cam == "tilt_up":
        z, y = "1.15", f"(ih-ih/zoom)*(1-on/{n})"
    elif cam == "static":
        z = "1.03"
    return f"scale={w*2}:{h*2},zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={w}x{h}:fps={FPS},format=yuv420p"


def ass_time(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


FONTS = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc",
         "/Library/Fonts/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]


def render_text_png(path, text, w, h, size, bottom_margin=None) -> None:
    """Transparent PNG the size of the frame with outlined white text (no libass/freetype filter needed)."""
    from PIL import Image, ImageDraw, ImageFont
    font = None
    for f in FONTS:
        try:
            font = ImageFont.truetype(f, size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default(size)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    words, lines, cur = text.split(), [], ""
    for wd in words:  # wrap to 85% of the frame width
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=font) <= w * 0.85 or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    lh = int(size * 1.25)
    block = lh * len(lines)
    y = (h - block) // 2 if bottom_margin is None else h - bottom_margin - block
    for ln in lines:
        x = (w - d.textlength(ln, font=font)) / 2
        d.text((x, y), ln, font=font, fill=(255, 255, 255, 255), stroke_width=max(2, size // 14), stroke_fill=(0, 0, 0, 255))
        y += lh
    img.save(path)


def subtitle_events(sb, durs, lengths, w, h, total_film, outdir, ar):
    """[(png, start, end)] for each narrated line and the end card."""
    wide = w > h
    size, margin = (44, 70) if wide else (46, 190)
    ev, t = [], 0.0
    for s in sb["shots"]:
        n = s["narration"]
        if n and lengths.get(s["id"]):
            a = t + n.get("delay_s", 0.5)
            png = outdir / f"sub_{s['id']}_{ar}.png"
            render_text_png(png, n["text_en"], w, h, size, margin)
            ev.append((png, a, a + lengths[s["id"]]))
        t += durs[s["id"]]
    png = outdir / f"sub_end_{ar}.png"
    render_text_png(png, sb["end_card"]["text_en"], w, h, 80 if wide else 84)
    ev.append((png, t, total_film))
    return ev


def measure_loudnorm(ff, wav) -> dict:
    import json as _j
    p = subprocess.run([ff, "-hide_banner", "-i", str(wav), "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    return _j.loads(p.stderr[p.stderr.rindex("{"):p.stderr.rindex("}") + 1])


def final() -> int:
    ff = shutil.which("ffmpeg")
    if not ff:
        print("ffmpeg not found on PATH.")
        return 1
    t0 = time.time()
    sb = load_storyboard()
    lengths = narration_lengths()
    kd = OUT / "keyframes"
    tmp = OUT / "final_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    durs = {s["id"]: effective_duration(s, lengths) for s in sb["shots"]}
    end_d = float(sb["end_card"]["duration_s"])
    total = sum(durs.values()) + end_d
    missing = [s["id"] for s in sb["shots"] if not (kd / f"{s['id']}_16x9.jpg").exists()]
    if missing:
        sys.exit(f"Missing keyframes for {missing}. Run: python pipeline/keyframes.py")

    # --- audio: narration track, score, ducking, two-pass loudnorm to -14 LUFS ---
    segs = []
    for s in sb["shots"]:
        n, wav, seg = s["narration"], OUT / "narration" / f"{s['id']}.wav", tmp / f"{s['id']}.wav"
        if n and wav.exists():
            run([ff, "-y", "-i", wav, "-af", f"aresample=48000,adelay={int(n.get('delay_s', 0.5) * 1000)}:all=1,apad=whole_dur={durs[s['id']]:.3f}",
                 "-ac", 1, "-t", f"{durs[s['id']]:.3f}", seg])
        else:
            run([ff, "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{durs[s['id']]:.3f}", seg])
        segs.append(seg)
    run([ff, "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{end_d:.3f}", tmp / "end.wav"])
    segs.append(tmp / "end.wav")
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segs), encoding="utf-8")
    narr = tmp / "narration_all.wav"
    run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", narr])

    music = OUT / "music" / "main.wav"
    if music.exists():
        music_src, music_note = ["-i", music], "supplied score file"
        mfx = f"[0:a]aresample=48000,aformat=channel_layouts=mono,atrim=0:{total:.3f},afade=t=in:d=2,afade=t=out:st={total-2:.3f}:d=2[m]"
    else:
        # Own synthesis (no third-party audio): a soft A-minor pad of sine tones, low-passed, no tremolo, kept quiet so it does not swell in pauses.
        tone = lambda f: ["-f", "lavfi", "-i", f"sine=frequency={f}:sample_rate=48000:duration={total:.3f}"]
        music_src = [*tone(110), *tone(164.8), *tone(220), *tone(261.6), *tone(329.6)]
        mfx = ("[0:a][1:a][2:a][3:a][4:a]amix=inputs=5:normalize=0,volume=0.045,lowpass=f=900,"
               f"afade=t=in:d=2,afade=t=out:st={total-2:.3f}:d=2,aformat=channel_layouts=mono[m]")
        music_note = "FFmpeg-synthesised placeholder pad"
    nin = 1 if music.exists() else 5
    mix = tmp / "mix_raw.wav"
    run([ff, "-y", *music_src, "-i", narr, "-filter_complex",
         f"{mfx};[{nin}:a]asplit=2[v1][v2];[m][v2]sidechaincompress=threshold=0.02:ratio=6:attack=300:release=1500[duck];"
         "[duck][v1]amix=inputs=2:normalize=0[a]", "-map", "[a]", "-ar", 48000, mix])
    m = measure_loudnorm(ff, mix)
    norm = tmp / "mix_norm.wav"
    run([ff, "-y", "-i", mix, "-af",
         f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
         f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true", "-ar", 48000, norm])
    print(f"Audio: score = {music_note}; loudness before {m['input_i']} LUFS -> target -14")

    # --- video per aspect ratio ---
    for ar, (w, h) in SIZES.items():
        clips = []
        for s in sb["shots"]:
            n = round(durs[s["id"]] * FPS)
            clip = tmp / f"{s['id']}_{ar}.mp4"
            run([ff, "-y", "-loop", "1", "-i", kd / f"{s['id']}_{ar}.jpg", "-vf", camera_filter(s["camera"], n, w, h),
                 "-frames:v", n, "-r", FPS, "-c:v", "libx264", "-preset", "veryfast", "-crf", 20, clip])
            clips.append(clip)
        run([ff, "-y", "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={FPS}", "-t", f"{end_d:.3f}",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", tmp / f"end_{ar}.mp4"])
        clips.append(tmp / f"end_{ar}.mp4")
        vl = tmp / f"vlist_{ar}.txt"
        vl.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in clips), encoding="utf-8")
        vid = tmp / f"video_{ar}.mp4"
        run([ff, "-y", "-f", "concat", "-safe", "0", "-i", vl, "-c", "copy", vid])
        ev = subtitle_events(sb, durs, lengths, w, h, total, tmp, ar)
        out = OUT / f"final_{ar}.mp4"
        inputs, chain, prev = [], [], "0:v"
        for k, (png, a0, b0) in enumerate(ev, start=2):
            inputs += ["-i", str(png)]
            chain.append(f"[{prev}][{k}:v]overlay=enable='between(t,{a0:.3f},{b0:.3f})'[v{k}]")
            prev = f"v{k}"
        p = subprocess.run([ff, "-y", "-i", str(vid), "-i", str(norm), *inputs, "-filter_complex", ";".join(chain),
                            "-map", f"[{prev}]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.3f}",
                            "-movflags", "+faststart", str(out)], capture_output=True, text=True)
        if p.returncode != 0:
            sys.exit("ffmpeg (subtitle overlay) failed:\n" + p.stderr[-1500:])
        print(f"{out}  ({total:.1f}s)")
    latency = round(time.time() - t0, 2)
    log_call(stage="assemble_final", model="ffmpeg", params={"total_s": round(total, 2), "score": music_note},
             seed=None, latency_s=latency, cost_usd=0.0, status="ok")
    print(f"Final cuts built in {latency}s")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["radio", "final"])
    a = ap.parse_args(argv)
    return radio() if a.cmd == "radio" else final()


if __name__ == "__main__":
    sys.exit(main())
