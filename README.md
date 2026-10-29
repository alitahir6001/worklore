# Worklore

Capturing the unwritten history of the team.

*Lore & Order for your work meetings.*

Drop meeting transcripts in, then ask across all of them: what was decided, who committed
to what, why a system works the way it does. Every answer cites the exact speaker turn it
came from. Meeting knowledge links to objects in your database-audit KB, so "where is BI
calculated?" returns the procedure, its dependencies, and the meeting where someone
explained why.

Your coding agent (Codex or Claude Code) is the interface. There's no server, no API key,
and no UI.

## Setup
```bash
uv sync                      # or: python -m venv .venv && .venv/bin/pip install -e . pytest
export WORKLORE_DATA=~/worklore-data   # outside this repo; enforced
export WORKLORE_KB=/path/to/kb         # read-only; fixtures/kb for the demo
uv run pytest
```

## Use
Drop `.docx` transcripts into `$WORKLORE_DATA/inbox/`, then in this repo ask your agent:
- "ingest new transcripts"
- "what did John say about integrations, and did it change?"
- "where is customer BI calculated and what depends on it?"

## Demo on synthetic data
```bash
uv run python fixtures/make_fixtures.py "$WORKLORE_DATA/inbox"
```
Then ingest, and check answers against `fixtures/gold_questions.md`.

## Data rule
Code goes here. Data never does. Work transcripts and the KB stay on the work machine.
Clone this repo there with a fine-grained GitHub token scoped to this repo with read-only
Contents access, so the work machine can pull but never push.

## Status
v1 POC: transcripts only. The docx layout and the KB adapter are stand-ins until the
`kb-survey` skill reports the real formats.
