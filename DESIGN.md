# DESIGN

## Brief (written before any generation)

> DRAFT by Claude from what Kenan said in chat. Kenan: confirm or correct the audience, the feeling and the logline.

- **Who watches:** Ethiopians and the Habesha diaspora, roughly 18 to 35, on their phones, plus curious viewers who have never sat through a coffee ceremony.
- **Where:** short vertical video feeds (9:16 first, 16:9 as well).
- **What they should feel at the end:** the unhurried warmth of a home where coffee is made for others; "I miss this" or "I want to sit at that table".
- **Logline:** Three cups of coffee turn a quiet morning into a blessing shared.
- **Source of the story:** the author's own memory of how Buhe is kept (details below). No single remembered night is claimed; the film shows a typical one.

## What the author told us about Buhe (considered first, not used in the final film)

- Mothers usually bake the mulmul, starting in the morning, on a traditional clay baking pan (shekla mitad), wrapped in koba leaves.
- The night before, the family gathers to light the chibo (a bonfire of bundled sticks).
- Groups of boys with long thin sticks go from house to house singing traditional Buhe songs.
- When mulmul or money is given, the boys sing a specific part of the song in response.
- Afterwards people clap and say "Amet amet yadrsln" (older people especially).
- Smell of smoke and food, laughter, singing from house to house; the mood is lively, warm, communal.
- The author wants the ending to be the family, the children and the chibo seen together, zoomed out.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-11-24 | Language: Amharic | Audience language; the brief says Gemini TTS covers Amharic (to be checked by ear). |
| 2026-11-24 | Subject: Buhe (first choice) | First-hand details, safe in public, visual (fire, bread, singing), has a built-in exchange (bread out, blessing back). |
| 2026-11-26 | Subject changed to the coffee ceremony | Scope. Buhe needs a crowd, fire, boys and a song. The ceremony has one place, one host and one pot, so fewer characters to keep consistent, which the brief recommends. About 13 hours were left. The first Buhe draft stays in git history. |
| 2026-11-24 | Characters are illustrated and invented; narrator is a stock TTS voice | No real person's face or voice is generated, so no consent gate (see ETHICS.md). |
| 2026-11-24 | Song handled as an experiment ladder (A: sung, B: chanted, C: percussion only) | Amharic singing in ACE-Step is unconfirmed. Lyrics must come from the author; none are written. |
| 2026-11-25 | Build the pipeline stage by stage, in the order of the brief's phases, and make the film with it | The brief asks for a film regenerable from `storyboard.json` with one command. |

## Ideation record (considered before choosing)

| Idea | Why not (or why) |
|---|---|
| Coffee ceremony | Chosen on 2026-11-26. Strong structure (three rounds: abol, tona, baraka), one place and few characters. The most familiar subject, so the personal angle must come from the author's own details. |
| Old Piassa (gold shops, baklava, the Arada building) | Rich, but the author's own details were second-hand, the street no longer exists in its old form, and the demolitions are politically sensitive. Kept as a "what I would build next" idea. |
| Ethiopian New Year (Enkutatash) | Risk of reading as a greeting card without a specific true moment. |
| Belay Zeleke | Powerful, but a person who died in 1945 cannot give consent, scope is too large for 60-90 s, the ending is politically charged, and the author named no personal link. |
| Buhe | Chosen first, then replaced by the coffee ceremony for scope (see decision log). |

## User test 1: radio cut

TO DO. Needs at least 3 people from the intended audience. Record here: who, what they said, where they reacted, what changes in `storyboard.json` because of it.

## User test 2: near-final cut

TO DO. Same format. Record what changed after test 1 and after test 2.

## Shot reasons

Each shot's reason is stored in `storyboard.json` (`reason` field) and is required by the schema.
