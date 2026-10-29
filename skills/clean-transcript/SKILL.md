---
name: clean-transcript
description: Clean a Worklore turn-tagged transcript (remove filler, fix Copilot transcription grammar) into turns.clean.md without changing meaning or turn structure. Used by the ingest skill; use directly when asked to clean a Worklore transcript.
---

# clean-transcript

Input: `sources/<source_id>/turns.raw.md`. Output: `sources/<source_id>/turns.clean.md`.

## Turn-ID contract (do not change; `lore validate` enforces it)
- Copy the header lines (`# title`, `source:`, `date:`, `project:`) unchanged.
- Exactly one output line per input turn, in the same order, each starting with the same
  `[tNNN] Speaker (HH:MM:SS): ` prefix, byte for byte.
- Never merge, split, drop, add, or reorder turns. A turn that is only filler stays, with
  its text reduced to what's left (e.g. `Okay.`); if nothing at all is left, write `(filler)`.
- Keep each turn's text on one line.

## Cleanup rules
<!-- PORT: replace this section with the rules from your work cleanup skill. Keep the
contract above. -->
- Remove filler and false starts: um, uh, you know, like (as filler), repeated words
  ("that's, that's" → "that's").
- Fix grammar and punctuation that Copilot mangled. Keep the speaker's own words and register.
- Never change meaning: names, numbers, dates, object names (`Schema.Object`), commitments,
  and hedges ("I think", "probably") stay exactly as said.
- If a phrase is garbled and its meaning is unclear, keep it and append `[unclear]`.
  Don't guess.
