# ETHICS

## Consent record
- No real person's face or likeness is generated or shown. Characters are illustrated, invented figures (`characters` in `storyboard.json`). "Emaye" in the story is an invented character, not a portrait of any real person.
- No real person's voice is cloned or imitated. Narration uses one stock Gemini TTS voice named in `storyboard.json`.
- No recordings of real people are used in the film.
- If any real person is later shown or voiced, their recorded consent is added here first.

## Licences and terms
| Item | Terms | Status |
|---|---|---|
| Gemini TTS output | Google Gemini API terms (free tier of the Gemini API; outputs may carry a SynthID/C2PA mark) | terms not read line by line by me; used as a personal learning project, not commercially |
| FLUX.1 schnell via Cloudflare Workers AI | The Cloudflare model page links to Black Forest Labs' terms of service (https://bfl.ai/legal/terms-of-service); the page names no licence itself | I did not read the linked terms in full; no commercial use is planned |
| FFmpeg (Homebrew build) | LGPL/GPL depending on build | not verified |
| Score | our own code-synthesised music (`pipeline/music.py`): krar-like plucked notes, kebero-like drum, quiet drone (a washint-like flute was tried and removed). It evokes these instruments; it is not a recording or an authentic model of them | no third-party audio |
| Third-party sound effects | none used | — |

## Labelling
- A 3 s end card reads "Made with AI" in both aspect ratios.
- The platform's AI / altered-content label is switched on when posting.
- Provenance marks (SynthID, and the C2PA chunk Gemini adds to its WAVs) are not stripped from raw model outputs; the final MP4 is re-encoded by FFmpeg, which does not carry the C2PA chunk over.
