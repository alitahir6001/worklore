---
name: ingest
description: Ingest new meeting transcripts from the Worklore inbox into the library (parse, clean, validate, extract records, index). Use when the user says "ingest new transcripts", "process the inbox", or drops a transcript into worklore.
---

# ingest

Run every step through `lore`; never hand-edit `meta.json`, `turns.raw.md`, or `lore.db`.

1. `lore status` lists the `.docx` files waiting in the inbox.
2. **Project tags, one confirmation for the whole batch.** For each file, run `lore peek <file>`.
   Then show the user one table: file, parsed date, proposed title, proposed project tag
   (reuse an existing tag from `lore status`/past sources when it fits). Wait for their
   confirmation or corrections. This is the only human checkpoint, because a wrong tag
   silently breaks filtering.
3. For each file: `lore parse <file> --project <tag> [--title "..."] [--date YYYY-MM-DD]`.
4. **Clean:** follow `skills/clean-transcript/SKILL.md` to write
   `sources/<source_id>/turns.clean.md` from `turns.raw.md`.
5. `lore validate <source_id>`. Fix only the cleaned file until it passes; never edit the raw one.
6. **Extract:** follow `skills/extract-records/SKILL.md` to write `records/<source_id>.jsonl`.
7. `lore validate <source_id>` again, and fix the records until it passes.
8. After the batch: run `lore index` once, then `lore status` to confirm nothing is left.
9. Report: sources added, turns, records by type, and any warnings from `lore index`.

If a file yields "No speaker turns found", stop and tell the user: the docx layout doesn't
match `parse_docx.HEADER`. Don't guess at a workaround.
