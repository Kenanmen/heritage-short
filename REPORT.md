# Buna: report

Kenan Mengistu. Repository: https://github.com/Kenanmen/heritage-short

## What I set out to make, and for whom
A 70-second illustrated short film about the Ethiopian coffee ceremony, narrated in Amharic with English subtitles, in 9:16 and 16:9. I am a native Amharic speaker; the story is a child's memory of waiting through three rounds of Emaye's coffee, and the third round is for him too. Audience: **TODO (Kenan, in your words): who you made it for and the one feeling you wanted at the end.** (The draft brief is in DESIGN.md and is not yet confirmed by me.)

## What I learned from my audience
**TODO after the user tests.** Test 1: who watched (number, relationship), what each said, what I changed because of it. Test 2: same for the revised version. Only real notes go here; the same facts go in DESIGN.md.
Reviewing the first full cut myself (not a user test) I found four problems and changed them: an unrelated picture at 13 s (s03), a pot drawn larger than the child (s06, s10), the speaker of "Wait, it's not time yet" shown as the child instead of the mother (s06), and a missing end-card text. Details in DESIGN.md.

## The hardest problem and how I solved it
Free-tier limits on Amharic text-to-speech. The model allowed 3 requests per minute and 10 per day; early runs hit 429 errors mid-batch (runs.jsonl). I added pacing (21 s between calls), a wait that honours the provider's retry delay, a stop on a daily-quota error and full error logging. I also dropped narration from two shots (s03, s08) so the seven remaining lines fitted the day's quota, which makes those two shots silent beats. Related failures I found and fixed: the style sentence was read aloud by the model (E02), and a click at the start and end of each clip came from a C2PA metadata chunk that was wrapped twice (FAILURES.md items 1 and 2).

## A suggested practice that helped, and one that did not
- **Helped (JSON contract plus hash cache):** TODO (Kenan: say what your instinct was). Evidence: changing one prompt in `storyboard.json` regenerates one shot only; the rest print "cached" (s06 regenerated alone on 26 Nov, see runs.jsonl).
- **Did not help or could not be tested (reference sheet before keyframes):** the Cloudflare FLUX.1 schnell endpoint takes no reference image, so I could not test it; consistency relied on one style block and mostly-from-behind characters. FLUX also rejected a seed (FAILURES.md item 9). Whether a different model with reference images would have kept the characters consistent is untested.

## Work beyond the minimum
- Compared three Amharic TTS models and had a native speaker judge them (E01), then found the English style prompt was being spoken (E02).
- Wrote my own score generator (krar-like plucks, kebero-like drum) instead of using a stock track; it evokes those instruments and is not authentic (ETHICS.md).
- Logged every model call with latency and redacted errors.
**TODO (Kenan): add anything you tested yourself that I have not listed.**

## What I would build next
Real moving shots with Wan 2.2 on a GPU (cut here for time, FAILURES.md item 6); a character reference sheet with a model that accepts reference images; narration for the two silent shots when quota allows; a stronger score from a music model; and a second language test.

## Honest limits
Fewer experiments have a recorded observation than the ten listed (see EXPERIMENTS.md TODO rows). Shots are stills with FFmpeg camera moves. The Amharic accent of every TTS model I tried was moderate.
