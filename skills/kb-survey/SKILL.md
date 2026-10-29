---
name: kb-survey
description: Survey the structure (never the content) of the existing database-audit KB repo, a Copilot transcript .docx, and this machine's agent setup, and write a placeholder-only report for porting Worklore to this machine. Use when the user says "run the kb survey" or "survey my KB for worklore".
---

# kb-survey

Produce `~/worklore-survey/kb-survey-report.md` describing **shapes, not values**. The user
reads it, redacts anything left, and carries it to another machine by hand.

## Hard rules
- Write the report ONLY to `~/worklore-survey/`. Never commit, push, upload, paste into a
  web tool, or send it anywhere.
- No real values: no object names, table names, people, companies, file contents, or
  transcript text. Use placeholders: `<str>`, `<int>`, `<bool>`, `<date>`, `<SPEAKER>`,
  `<TEXT>`, `<SCHEMA>.<OBJECT>`.
- JSON keys, file extensions, counts, and sizes are fine. If a key itself looks sensitive
  (a client or product name), replace it with `<key>` and say so.
- Read-only. Change nothing in the KB, the transcript, or the agent config.

## Inputs (ask the user for any you don't have)
1. Path to the KB repo.
2. Path to one Copilot transcript `.docx` (raw, not cleaned).
3. Path to the installed transcript-cleanup SKILL.md.

## Sections to produce

### 1. KB inventory
Directory tree (2 levels, folder names only if they're generic, else `<dir>`), file
counts and total size per extension.

### 2. Structured files (.json / .jsonl / .csv)
For each distinct file *kind* (group files with the same keys):
- File-name pattern (e.g. `objects/*.jsonl`) and record count.
- Keys with types, including nested keys. Mark which keys are always present.
- One example record with every value replaced by a placeholder.
- **Object IDs:** which key identifies a DB object, its pattern (e.g. `<SCHEMA>.<OBJECT>`,
  `[<SCHEMA>].[<OBJECT>]`, `<DB>.<SCHEMA>.<OBJECT>`), and whether the same object uses the
  same ID string in every file kind. Check this on 5 objects by comparing, then report
  only yes/no and the pattern.
- **Dependencies:** how an edge is represented (keys for from/to/type), the distinct edge
  type values and their counts (type values are fine to show if generic like
  `calls`/`reads`; else `<edge_type_N>`), and whether any edge marks dynamic SQL or
  where the edges came from (e.g. `sys.sql_expression_dependencies`, parsed definitions,
  manual).

### 3. Unstructured files (.md / .txt)
Per kind: purpose in one generic line (e.g. "one file per stored procedure: summary +
parameters"), heading outline with placeholder text, and whether they reference object
IDs in the same pattern as section 2.

### 4. Copilot transcript .docx structure
Use python-docx if available, else unzip `word/document.xml`. Report:
- The first ~12 paragraphs as `[n] style=<style> | <shape>`, where shape replaces text
  with placeholders but keeps separators exactly, e.g. `<SPEAKER>\t<TIMESTAMP>` or
  `<SPEAKER>   <TIMESTAMP>` (show tabs as `\t`, count spaces).
- Timestamp format (e.g. `m:ss`, `h:mm:ss`, `0:00:03.120 --> 0:00:05.000`).
- Whether a turn's text is one paragraph or can span several.
- Any preamble before the first turn (title, date, attendees), as placeholders, with the
  date format.
- Tables, headers/footers, or anything else in the document, if present.

### 5. Agent environment
- `codex --version`, and whether `codex exec --help` works.
- Where this Codex loads skills from: report the directory the installed cleanup skill
  lives in, plus any skills/AGENTS.md locations `codex --help` or `~/.codex/` show.
- `python3 --version`; `python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('create virtual table t using fts5(x)')"`
  (fts5 ok / error); whether `pip`, `uv`, and `git` exist.
- Whether an MCP server for the live DB is configured (name and "read-only: yes/no" only,
  no connection strings).

### 6. Cleanup skill
Its path only. The user copies its text over manually.

## Before finishing
1. Self-check: list every token in the report that is not a JSON key, file extension,
   placeholder, number, or generic word. For each, confirm it's safe or replace it.
2. Tell the user: "Report at ~/worklore-survey/kb-survey-report.md. Read all of it before
   copying it anywhere; you're the last check."
