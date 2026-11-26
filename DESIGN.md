# DESIGN

## Brief (written before any generation)

> DRAFT by Claude from what Kenan said in chat. Kenan: confirm or correct the audience, the feeling and the logline.

- **Who watches:** Ethiopians and the Habesha diaspora, roughly 18 to 35, on their phones, plus curious viewers who have never sat through a coffee ceremony.
- **Where:** short vertical video feeds (9:16 first, 16:9 as well).
- **What they should feel at the end:** the unhurried warmth of a home where coffee is made for others; "I miss this" or "I want to sit at that table".
- **Logline:** A child waits through three rounds of Emaye's coffee, and the third is for him too.
- **Source of the story:** the general shape of the Ethiopian coffee ceremony (roasting, pounding, the clay pot, three rounds: abol, tona, baraka). From the author: his mother (Emaye) makes the coffee; he remembers the sound of the roasting and being told to wait. The rest (the three rounds, the objects) is general knowledge of the ceremony. The payoff in s09, that the child gets a cup in the third round, is a story beat proposed by Claude and still needs the author's confirmation.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-11-24 | Language: Amharic | Audience language; the brief says Gemini TTS covers Amharic (to be checked by ear). |
| 2026-11-26 | Subject: the coffee ceremony | One place, one host and one pot, so few characters to keep consistent (the brief recommends this), a clear structure of three rounds, and a subject the audience knows. |
| 2026-11-24 | Characters are illustrated and invented; narrator is a stock TTS voice | No real person's face or voice is generated, so no consent gate (see ETHICS.md). |
| 2026-11-25 | Build the pipeline stage by stage, in the order of the brief's phases, and make the film with it | The brief asks for a film regenerable from `storyboard.json` with one command. |
| 2026-11-26 | One narrator voice for the whole film | After hearing the first radio cut, Kenan found the mix of a man's and a woman's voice confusing: nothing in the sound said who was speaking. |
| 2026-11-26 | Narration rewritten as one first-person memory of Emaye (waiting, then the third round), using the author's own details | The author said a list of descriptions "doesn't feel like a narration" and asked for continuous narration of the actions. |
| 2026-11-26 | Narration lines replaced by a revised set, proofread with help from a second AI assistant and approved by Kenan (a native Amharic speaker) | Kenan found the first draft read like a step-by-step explanation. The revised lines are shorter and more personal. The English subtitles were rewritten from the new Amharic by Claude and still need Kenan's check. |
| 2026-11-26 | Shots s03 and s08 carry no narration (picture and score only); the other 8 lines stay | The free-tier Gemini TTS quota is 10 requests per day per model (AI Studio rate-limit page). After testing, about 7 requests were left for 9 lines. Kenan chose to drop two lines and keep one voice, over mixing in a second model for two lines. Shot lengths are unchanged, so the film stays at 67 s (70 s with the end card). |
| 2026-11-26 | Fuller narration (10 connected lines, one per shot, plus a closing line) instead of 7 very short lines | The first radio cut did not make sense to its first listener (Kenan): 7 lines of 2 to 4 words carried no story. Chosen while accepting the free-tier risk of ~10 TTS calls per full run; fall back to fewer lines if the quota blocks us. |

## Ideation record

| Idea | Why not (or why) |
|---|---|
| Coffee ceremony | Chosen. Strong three-round structure, one place, few characters. The most familiar subject, so the personal angle must come from the author's own details. |
| Old Piassa (gold shops, baklava, the Arada building) | Rich, but the author's details were second-hand, the street no longer exists in its old form, and the demolitions are politically sensitive. |
| Ethiopian New Year (Enkutatash) | Risk of reading as a greeting card without a specific true moment. |
| Belay Zeleke | Powerful, but a person who died in 1945 cannot give consent, scope is too large for 60-90 s, and the author named no personal link. |

## User test 1: radio cut

TO DO. Needs at least 3 people from the intended audience. Record here: who, what they said, where they reacted, what changes in `storyboard.json` because of it.

## User test 2: near-final cut

TO DO. Same format. Record what changed after test 1 and after test 2.

## Shot reasons

Each shot's reason is stored in `storyboard.json` (`reason` field) and is required by the schema.

## Change after the author reviewed the first full cut (Thu 26 Nov, evening)
The author (not a test group) watched the 70 s film and reported: the picture at 13 s (s03) did not relate to the story, the picture at 32 s (s06) and the last picture (s10) showed the coffee pot bigger than the child, and the end card showed no text.
- s03: prompt rewritten so the picture shows one clear action (the host holding the roasted beans, smoke rising, guests waving it toward themselves).
- s06 and s10: prompts now state the pot's scale (about the size of the child's lap, tiny next to the people). FLUX has no sense of scale on its own, so this is a prompt change, not a guarantee; each regeneration is a new random draw.
- End card: text overlay hardened (looped PNG inputs) after the text did not show on the author's FFmpeg.
- Score: author asked for something less bland; replaced the plain pad with our own synthesised krar-like plucks and kebero-like drum. A flute was tried and removed because the author heard a disturbing noise.
Narration was not changed (free-tier quota for the day was spent).
