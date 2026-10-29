# Worklore: agent rules

Worklore is a queryable library of the user's work meetings: transcripts parsed into speaker
turns, plus extracted records (decisions, action items, facts, open questions) that cite
those turns and link to objects in the database-audit KB.

## Where things live
- **Code:** this repo. **Data:** `$WORKLORE_DATA` (default `~/worklore-data`), which is
  never inside this repo. **KB:** `$WORKLORE_KB`, read-only.
- Files are the truth: `sources/<id>/` (raw.docx, meta.json, turns.raw.md,
  turns.clean.md) and `records/<id>.jsonl`. `lore.db` is derived; `lore index` rebuilds it.

## Rules
- Read and query the library only through `lore` (`uv run lore ...` or the installed
  `lore`). Never bulk-read the data folder into context.
- Every claim in an answer cites turn IDs (`<source_id>#tNNN`) you actually read.
- Never invent owners, dates, decisions, or rationale. Mark inferences as inferred.
- When sources disagree or something changed, show both versions with dates.
- Never edit `turns.raw.md`, `raw.docx`, `meta.json`, or another source's record file.
- Never commit, copy, upload, or paste anything from the data folder or the KB outside this
  machine. Work data stays on the work machine.

## Skills (read the file when the task matches)
| Task | Skill |
|---|---|
| Ingest transcripts from the inbox | `skills/ingest/SKILL.md` |
| Clean a transcript | `skills/clean-transcript/SKILL.md` |
| Extract records | `skills/extract-records/SKILL.md` |
| Answer a question from the library | `skills/ask/SKILL.md` |
| Survey the KB/transcript/agent setup for porting | `skills/kb-survey/SKILL.md` |

## Commands
`lore status | peek | parse | validate | index | search | records | turns | kb`. Run
`lore <cmd> -h` for flags. Tests: `uv run pytest`.
