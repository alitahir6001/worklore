---
name: extract-records
description: Extract decisions, action items, facts, and open questions from a cleaned Worklore transcript into records/<source_id>.jsonl, each cited to turn IDs and linked to KB objects. Used by the ingest skill; use directly when asked to extract records from a Worklore source.
---

# extract-records

Read `sources/<source_id>/turns.clean.md`. Write `records/<source_id>.jsonl`, one JSON
object per line. Extract only what someone would want to look up later, not every turn.
Ten good records beat forty thin ones. An empty file is valid for a meeting with nothing durable.

## Record shape
```json
{"id": "<source_id>#r01", "type": "decision", "text": "...", "basis": "canon",
 "evidence": ["<source_id>#t007"], "speakers": ["Jane Smith"],
 "owner": "Jane Smith", "due": "2026-10-03", "status": "open",
 "subjects": [{"kind": "kb_object", "ref": "Reporting.usp_CalcCustomerBI"},
              {"kind": "project", "ref": "chatbot"}],
 "observed_at": "<meeting date>", "supersedes": [], "conflicts_with": []}
```
- `type`: `decision` (a choice made, plus its rationale if stated) | `action_item` (someone
  committed to doing something) | `fact` (how a system, process, or object works or why it
  is the way it is) | `open_question` (something unresolved; say what would answer it).
- `text`: one self-contained sentence, readable without the transcript. Put the rationale
  in the same text when it was stated.
- `evidence`: the turn IDs that support the text. Required.
- `basis`: `canon` only when the cited turns say it outright; `inferred` when you're connecting dots.
- `speakers`: who said it, exactly as named in the transcript.
- `owner` / `due`: only when stated in the cited turns. Never infer either. Convert spoken
  dates ("October 3rd") to `YYYY-MM-DD` using the meeting's year.
- `status`: `open` for action items and open questions when extracted.
- `observed_at`: the meeting date.

## Linking (this is the point of the library)
- **KB objects:** for every database object mentioned, run `lore kb <name>` to get the exact
  ID (it suggests matches for partial names) and use that as the `kb_object` ref. If it
  isn't in the KB, use `{"kind": "system", "ref": "<name as said>"}` instead.
- **Earlier records:** for each subject, run `lore records --subject <ref>` (and
  `lore records --q "<keywords>"`). If the new record changes an earlier one, add its ID
  to `supersedes`. If it disagrees and it's unclear which is right, use `conflicts_with`.
  If a new record resolves an earlier `open_question`, the new record `supersedes` it.
  Never edit older record files; new records carry the links.

Finish with `lore validate <source_id>`.
