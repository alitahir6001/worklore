# Handoff — live state snapshot

## Last updated
2026-10-29, session 1 (grilling → plan → v1 POC build → push)

## Current state
Worklore v1 POC is built and pushed to github.com/alitahir6001/worklore (`main` = a885747, 29 one-file commits on the user's Initial commit). It has the `lore` CLI, 5 skills, synthetic fixtures, and 27 passing tests. A deterministic CLI smoke test passed end to end; the agent-driven test (Claude cleans, extracts, and answers `fixtures/gold_questions.md`) has NOT been run. `parse_docx.HEADER` (Copilot docx layout) and `kb.FixtureKB` (KB shape) are stand-in guesses waiting on the `kb-survey` report from the work laptop. `.ai/` is uncommitted.

## Active task
Phase C: port to the work machine and prove the POC on real data.
Why: the pass bar is 10+ real transcripts and 5 questions with known answers (scenario 1: "what did X say about Y across meetings"; scenario 2: "where is BI calculated, what depends on it, and why"). Pass means at least 4/5 correct, with turn-ID citations that resolve.
Refs: brief `~/Desktop/projects/personal_work_knowledge_system_project_brief.md`; plan `~/.claude/plans/nested-gathering-pearl.md`.
1. [ ] user: clone on the work laptop (fine-grained read-only token if the repo is private), `uv sync`, `uv run pytest` (expect 27 passed), set `WORKLORE_DATA` (outside the repo) and `WORKLORE_KB`.
2. [ ] user: `uv run lore peek <real copilot .docx>`. Does the turn layout parse?
3. [ ] user: in Codex, run "Read skills/kb-survey/SKILL.md and follow it" with the KB, transcript, and cleanup-skill paths. Review `~/worklore-survey/kb-survey-report.md` and bring back the report plus the cleanup skill text by hand.
4. [ ] user (optional): Codex demo on fixtures in a separate `~/worklore-demo` data folder, scored against the gold questions.
5. [ ] agent: fix `parse_docx.HEADER` and the date patterns to the real layout; update `fixtures/make_fixtures.py` to match.
6. [ ] agent: write the real KB adapter in `kb.py`, keeping the methods `ids/get/find/edges_of`.
7. [ ] agent: port the cleanup rules into `skills/clean-transcript` (keep the turn-ID contract); set up the Codex skill path the survey reports.
8. [ ] user: ingest 10+ real transcripts at work, write 5 real questions with known answers, score them.
Also offered, not run: the agent end-to-end test on fixtures here, on Sonnet. It uses Pro usage, so ask first.

## Open threads
- Data rule: work data never enters the repo, including this file when on the work machine. Work → personal only as a report the user reviews and cleans up by hand.
- Teams/email are v2: they need Microsoft Graph consent through the sysadmin, and the user should ask early. Codex has no M365 connector today.
- Deviations from the plan: `lore index` always does a full rebuild (there's no `rebuild` command); records link back with `supersedes`/`conflicts_with` (append-only); dedupe hashes the parsed turns, not the file bytes.
- `codex exec` (background ingest) is unverified; survey section 5 answers it.
- Commits: the agent commits/pushes only when explicitly asked (it did once, on request).

## Next recommended step
The user runs steps 1–4 on the work laptop, then starts a fresh session here with the survey report and the cleanup skill text.

## Out of scope
Teams/email/calendar, embeddings, a UI (leaning local-only per teammate later), multi-user, headless batch ingest.
