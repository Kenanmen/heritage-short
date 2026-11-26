# ARCHITECTURE

`storyboard.json` (validated by `schema/storyboard.schema.json` plus semantic checks in `pipeline/common.py`) feeds independent stages. Each stage reads only the storyboard and the previous stage's files, so one stage can rerun alone.

| Stage | Script | Input -> output | Model / tool |
|---|---|---|---|
| validate | `pipeline/validate.py` | storyboard -> pass/fail (unique ids, speaker exists, total 60–90 s) | jsonschema |
| narration | `pipeline/narration.py` | `text_am` -> `outputs/narration/sNN.wav`, `timing.json` | Gemini TTS (REST) |
| keyframes | `pipeline/keyframes.py` | `image_prompt` + style block -> `outputs/keyframes/sNN{,_16x9,_9x16}.jpg` | Cloudflare FLUX.1 schnell |
| radio | `pipeline/assemble.py radio` | narration -> audio-only check cut | FFmpeg |
| final | `pipeline/assemble.py final` | keyframes + narration + score -> `final_16x9.mp4`, `final_9x16.mp4` | FFmpeg |

**Contracts.** Cache key per output = sha256 of that stage's inputs, stored in a `.meta.json` sidecar. Changing one prompt or line invalidates only that shot. Shot length = max(storyboard duration, delay + narration length + 0.4 s).
**Failure handling.** Every model call goes through `call_with_retries` (backoff, honours Google's `retryDelay`, stops on a daily quota) and is appended to `runs.jsonl` with latency, status and a redacted error. Narration paces calls 21 s apart for the 3 requests/min limit.
**Audio.** Score ducked under narration with sidechain compression (threshold 0.02, ratio 6, attack 300 ms, release 1500 ms), then two-pass loudnorm to -14 LUFS.
**Subtitles.** English only, from `text_en`, burned in from a generated ASS file with a larger bottom margin for 9:16. End card text from `end_card`.
**Secrets.** `.env` (git-ignored).
