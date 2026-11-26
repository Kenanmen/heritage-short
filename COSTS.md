# COSTS
Source of truth: `runs.jsonl` (latency per call; `cost_usd` is 0.0 on free tiers). Everything was on free tiers.

| Stage | Tool | Calls | Measured latency | GPU minutes | List-price equivalent |
|---|---|---|---|---|---|
| Narration | Gemini TTS | see runs.jsonl (E01/E02 3–7 s each, 2.5–5.6 s for 3.x) | 2.4–6.7 s per call | n/a | not computed |
| Keyframes | Cloudflare Workers AI FLUX.1 schnell | 10 shots + 8 experiments | see runs.jsonl after running | n/a | not computed |
| Moving shots | not used (FFmpeg Ken Burns) | 0 | ~50 s CPU for both cuts (test build) | 0 | $0 |
| Music | not used (FFmpeg synthesis) | 0 | seconds | 0 | $0 |
| Assembly | FFmpeg (local) | 1 | see `assemble_final` in runs.jsonl | n/a | $0 |

Free-tier limits found: Gemini TTS 3 requests/min and 10 requests/day per model (AI Studio rate-limit page, checked 2026-11-26). The daily reset time (believed midnight Pacific) is unverified. Cloudflare Workers AI free allowance: not looked up; check before relying on it.
