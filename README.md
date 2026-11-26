# Buna — an AI-generated short film about the Ethiopian coffee ceremony

Amharic narration, English subtitles, 60–90 s, in 16:9 and 9:16. Illustrated invented characters only.
Logline: *A child waits through three rounds of Emaye's coffee, and the third is for him too.*

## Reproduce the film from a clean clone

```
git clone https://github.com/Kenanmen/heritage-short && cd heritage-short
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
brew install ffmpeg                      # any build with the overlay filter (subtitles are drawn with Pillow)
cp .env.example .env                     # fill GEMINI_API_KEY, CF_ACCOUNT_ID, CF_API_TOKEN
python film.py                           # validate -> narration -> keyframes -> radio cut -> final
```
Output: `outputs/final_16x9.mp4`, `outputs/final_9x16.mp4`. Unchanged stages are skipped (cache by input hash), so a rerun costs no quota.
Regenerate one shot only: `python film.py keyframes --only s06` then `python film.py final`; one line: `python film.py narration --only s02`.

## Map
`storyboard.json` is the contract (checked against `schema/`). `pipeline/` has one script per stage. `runs.jsonl` logs every model call. Documents: DESIGN, ARCHITECTURE, EXPERIMENTS, FAILURES, COSTS, ETHICS.

## Honest scope
Shots are stills with FFmpeg camera moves (Ken Burns), not Wan 2.2 video, and the score is synthesised by our own code (`pipeline/music.py`). Why: see FAILURES.md.
