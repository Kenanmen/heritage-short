# DESIGN

## Brief (written before any generation)

> DRAFT by Claude from what Kenan said in chat. Kenan: confirm or correct the audience, the feeling and the logline.

- **Who watches:** Ethiopians and the Habesha diaspora, roughly 18 to 35, on their phones, plus curious viewers who have never sat through a coffee ceremony.
- **Where:** short vertical video feeds (9:16 first, 16:9 as well).
- **What they should feel at the end:** the unhurried warmth of a home where coffee is made for others; "I miss this" or "I want to sit at that table".
- **Logline:** Three cups of coffee turn a quiet morning into a blessing shared.
- **Source of the story:** the general shape of the Ethiopian coffee ceremony (roasting, pounding, the clay pot, three rounds: abol, tona, baraka). The author has not yet added details of his own family's ceremony; this draft uses general knowledge and the author must correct it.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-11-24 | Language: Amharic | Audience language; the brief says Gemini TTS covers Amharic (to be checked by ear). |
| 2026-11-26 | Subject: the coffee ceremony | One place, one host and one pot, so few characters to keep consistent (the brief recommends this), a clear structure of three rounds, and a subject the audience knows. |
| 2026-11-24 | Characters are illustrated and invented; narrator is a stock TTS voice | No real person's face or voice is generated, so no consent gate (see ETHICS.md). |
| 2026-11-25 | Build the pipeline stage by stage, in the order of the brief's phases, and make the film with it | The brief asks for a film regenerable from `storyboard.json` with one command. |

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
