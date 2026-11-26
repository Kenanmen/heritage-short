# EXPERIMENTS
Format: ID, hypothesis, one change (seed fixed), result, decision. Results come from `runs.jsonl` and the author's listening/viewing notes; nothing is claimed that was not run.

## Results (every call is in runs.jsonl)

| ID | Hypothesis | Change (one thing) | Result | Decision |
|---|---|---|---|---|
| E01 | Gemini TTS models pronounce the greeting and "jebena" intelligibly in Amharic | Same 3 shots, three models | 3.8 flash and 3.8 flash-lite returned audio for all shots; gemini-2.5-flash returned no audio on 3 calls (finishReason OTHER). Author heard a moderate accent on every model | Drop 2.5; use 3.x |
| E02 | A style instruction improves warmth | Same text with and without a style prefix | The English style text was read aloud by the models and inflated the clip | Stop sending style text |
| E03 | The 3.1 flash TTS model passes the smoke test within the free quota | Smoke test on gemini-3.1-flash-tts-preview | Passed; limit of 10 requests/day read from the AI Studio rate-limit page | Use it for the final narration |
| E04 | The shared style block makes keyframes look like one film | s06 with vs without style_block | The author judged the picture with the style block (A) better (`e04_style_block`) | Keep the style block in every prompt |
| E05 | 8 steps instead of 6 gives clearly better detail | s06, steps 6 vs 8 | The author preferred 6 steps (A) over 8 (`e05_steps`); 8 steps gave no improvement he could see | Keep 6 steps (faster) |
| E06 | The same prompt and steps give a similar picture on a second run (no seed is possible, see FAILURES 9) | s06 generated twice | Observation by the assistant (the author asked it to look): the composition was similar (a woman seen from behind, raised hand, pot on charcoal, steam) but the details differed: hair (bun vs white head wrap), dress cut, stool, wall colour, and the pot shape (a two-handled urn vs a spouted metal pot, neither a true jebena); the second picture also has a faint signature-like mark at the right edge. So the same prompt does not reproduce the same character (`e06_repeat`) | Never regenerate a shot casually; rely on the cache for stability; check each regenerated picture for stray marks and pot shape |
| E07 | The "Avoid:" text reduces unwanted faces and text | s06 with vs without Avoid | The author judged the picture with the "Avoid" text (A) better (`e07_negative`) | Keep the "Avoid" text |
| E08 | Stating the pot's scale in the prompt keeps the pot smaller than the child | s06 old child prompt vs the same child prompt with scale words | The author judged the pot smaller relative to the child in the scale-words picture (B) (`e08_scale`) | Keep scale words in prompts |
| E09 | A lighter, faster duck (ratio 3, 100/600 ms) is as clear as our starting values (ratio 6, 300/1500 ms) | Same narration and score, two ducking settings | The author judged the film's own setting (A) clear: the music gets quieter when the voice speaks. He gave no separate verdict on B, so no claim is made that A beats B (`e09_ducking`, `python pipeline/compare_ducking.py`) | Keep A (ratio 6, 300/1500 ms) |
| E10 | Centre-cropping the square FLUX picture to 9:16 keeps the subject in frame | Compare final_9x16 against final_16x9 for each shot | The author watched the vertical film and reported that no subject was cut off | Keep the centre crop |

Not run, no result claimed: ACE-Step candidates, Wan draft resolution, separate voices. Rows marked TODO count only after the author gives a real observation.
