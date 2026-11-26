# COSTS
Source of truth: `runs.jsonl` (one line per call; `cost_usd` is 0.0 because everything ran on free tiers). Latencies below are medians computed from it on 26 Nov 2026. Prices checked on 26 Nov 2026 on the providers' pages (links at the end).

| Stage | Tool | Successful calls | Measured latency (median, min to max) | GPU minutes | List-price equivalent |
|---|---|---|---|---|---|
| Narration (final) | Gemini TTS, gemini-3.1-flash-tts-preview | 8 | see note 1: 3.5 to 3.9 s for the two calls that were not paced | none on my side | about $0.015 for about 29 s of speech (note 2) |
| Narration (E01/E02/smoke) | gemini-3.8-flash-tts / flash-lite / 2.5-flash | 20 | 3.4 s (2.4 to 5.6 s) | none | not computed |
| Keyframes | Cloudflare Workers AI, flux-1-schnell | 14 for the film (10 shots plus regenerations), 11 for experiments and the smoke test | 2.9 s (2.1 s to 24 s; the 24 s call included a retry) | none | about $0.00085 per 1024x1024 image at 6 steps, so about $0.02 for all 25 images (note 3) |
| Moving shots | not used (FFmpeg camera moves on stills) | 0 | n/a | 0 | $0 |
| Music | our own synthesis, `pipeline/music.py` | 1 | 3.0 s on the author's Mac | 0 | $0 |
| Assembly | FFmpeg, local, both aspect ratios | 4 | 48 s (28 to 55 s) | 0 | $0 |

Total list-price equivalent for everything generated: under $0.10. Actual cost: $0.

**Note 1, a measurement flaw I found and fixed.** For the final narration run, the logged latency of most calls is 20.6 to 21.4 s, because my code slept 21 s for the free-tier rate limit inside the timed call. So those numbers are wait plus API time and are not the API time. I moved the pacing wait before the timed call (commit after b1ad719); runs after that log the API time only. The only two final-run calls without a wait were 3.5 s and 3.9 s, in line with the unpaced calls in E01/E02 (2.4 to 5.6 s). I did not rerun the narration to re-measure, because the daily free quota was spent.
**Note 2.** $1.00 per 1M text input tokens and $20.00 per 1M audio output tokens (paid tier). I assumed 25 audio tokens per second; I did not verify that rate, so this is an estimate.
**Note 3.** $0.0000528 per 512x512 tile (a 1024x1024 image is 4 tiles) plus $0.0001056 per step. Assumes 1024x1024 output; I did not check the output size on the response, and experiment E05 used 8 steps for some images.

## Free-tier limits found
- Gemini TTS (AI Studio rate-limit page, read 26 Nov 2026): 3 requests per minute and 10 requests per day per model. The reset time (believed midnight Pacific) is unverified.
- Cloudflare Workers AI: 10,000 neurons per day free; $0.011 per 1,000 neurons above that (Cloudflare pricing page, read 26 Nov 2026). 25 flux-1-schnell images used well under 1% of that at the listed rates.
- Gemini 3.1 Flash TTS preview has a free tier ("Free of charge" for input and output on ai.google.dev/pricing, read 26 Nov 2026).

## Frontier comparison
None: I had no access to a paid frontier image, video or TTS model. The only comparison is between Gemini TTS models (E01).

Sources: https://developers.cloudflare.com/workers-ai/platform/pricing/ , https://developers.cloudflare.com/workers-ai/models/flux-1-schnell , https://ai.google.dev/pricing
