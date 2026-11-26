# EXPERIMENTS
Format: ID, hypothesis, one change (seed fixed), result, decision. Results come from `runs.jsonl` and the author's listening/viewing notes; nothing is claimed that was not run.

## Results (every call is in runs.jsonl)

| ID | Hypothesis | Change (one thing) | Result | Decision |
|---|---|---|---|---|
| E01 | Gemini TTS models pronounce the greeting and "jebena" intelligibly in Amharic | Same 3 shots, three models | 3.8 flash and 3.8 flash-lite returned audio for all shots; gemini-2.5-flash returned no audio on 3 calls (finishReason OTHER). Author heard a moderate accent on every model | Drop 2.5; use 3.x |
| E02 | A style instruction improves warmth | Same text with and without a style prefix | The English style text was read aloud by the models and inflated the clip | Stop sending style text |
| E03 | The 3.1 flash TTS model passes the smoke test within the free quota | Smoke test on gemini-3.1-flash-tts-preview | Passed; limit of 10 requests/day read from the AI Studio rate-limit page | Use it for the final narration |
| E04 | The shared style block makes keyframes look like one film | s06 with vs without style_block | TODO: author's viewing note (`outputs/experiments/e04_style_block`) | TODO |
| E05 | 8 steps instead of 6 gives clearly better detail | s06, steps 6 vs 8 | TODO (`e05_steps`) | TODO |
| E06 | The same prompt and steps give a similar picture on a second run (no seed is possible, see FAILURES 9) | s06 generated twice | TODO (`e06_repeat`) | TODO |
| E07 | The "Avoid:" text reduces unwanted faces and text | s06 with vs without Avoid | TODO (`e07_negative`) | TODO |
| E08 | Stating the pot's scale in the prompt keeps the pot smaller than the child | s06 old prompt vs new prompt with scale words | TODO: author's viewing note (`e08_scale`; the old-prompt picture is from the first run) | TODO |
| E09 | A lighter, faster duck (ratio 3, 100/600 ms) is as clear as our starting values (ratio 6, 300/1500 ms) | Same narration and score, two ducking settings | TODO: author's listening note (`e09_ducking`, `python pipeline/compare_ducking.py`) | TODO |
| E10 | Centre-cropping the square FLUX picture to 9:16 keeps the subject in frame | Compare final_9x16 against final_16x9 for each shot | TODO: author's viewing note | TODO |

Not run, no result claimed: ACE-Step candidates, Wan draft resolution, separate voices. Rows marked TODO count only after the author gives a real observation.
