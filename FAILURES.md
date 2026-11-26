# FAILURES
Format: what broke, what I tried, what fixed it. Evidence is in `runs.jsonl`.

1. **Style text spoken aloud.** A style sentence prefixed to the TTS prompt was read out (and inflated the clip). Fix: the style text is no longer sent (E02).
2. **Click and noise at clip start/end.** Gemini 3.x returns a full WAV with a trailing C2PA chunk; wrapping it again made a click. Fix: `save_audio` keeps the API's RIFF as sent; `repair_wrapped_wav` repairs older clips.
3. **gemini-2.5-flash-preview-tts returned no audio** (finishReason OTHER) for several shots in E01/E02. Fix: the final run uses the 3.x model; the error text is now logged.
4. **Free-tier quota (3 requests/min, 10/day per TTS model).** 429s hit mid-run. Fix: 21 s pacing, retryDelay wait, stop on daily quota, full error body logged. Workaround that costs the film something: shots s03 and s08 have no narration (silent beats) so the 7 remaining lines fit the day's quota. Decision in DESIGN.md.
5. **Wrong test lines in the log.** I (the assistant) wrote two fake lines into `runs.jsonl` while testing; they were removed (commit 4dcd7cd) and disclosed.
6. **Wan 2.2 moving clips and ACE-Step score not done.** Kaggle GPU setup and generation did not fit the remaining time after the deadline was moved closer (one hour left on the final day). Workaround: FFmpeg Ken Burns moves on stills and a synthesised pad. The film has less motion and a plainer score than planned.
7. **Amharic accent.** All TTS models tried had a moderate accent; the native-speaker author judged it acceptable ("acceptable") rather than good.
8. **Character consistency.** FLUX.1 schnell takes no reference image; consistency relies on one style block, and shots that show the characters mostly from behind or as hands.
9. **No seed on Cloudflare flux-1-schnell.** My first keyframe run failed with HTTP 400 (`/seed` not allowed). I removed the seed; a changed prompt is a new random draw, and the hash cache keeps unchanged shots identical. The `seed` field in storyboard.json is therefore not used by the keyframe stage.
10. **My FFmpeg build had no `subtitles` filter** (`No such filter: 'subtitles'` on the author's Mac, FFmpeg 9.1 without libass). Fix: subtitles and the end card are drawn as transparent PNGs with Pillow and laid over the video with FFmpeg's `overlay` filter, so the build only needs core filters. Pillow was added to requirements.txt.
11. **Latency in runs.jsonl was inflated by my own pacing.** The final narration run logged about 21 s per call because the 21 s free-tier wait sat inside the timed call. Fixed by pacing before the timed call; documented in COSTS.md note 1. I did not rerun the narration to re-measure (the day's free quota was spent).
