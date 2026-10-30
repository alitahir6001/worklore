# Project rules & how to maintain .ai/

## Maintaining these files
At session start, read `handoff.md` ONLY. Everything else loads on demand.

- **handoff.md** - live state snapshot, and the only file read at startup. Rewrite in place, never append like a log. Cap 8 KB.
- **rules.md** - this file. Read when you're about to change code, or when handoff points at a rule. Edit only on an explicit "add a project rule: X".
- **backlog.md** - parked work. Read only when the user asks about it or asks you to add to it. Never read at startup.
- Permanent gotchas / non-obvious behavior that stays true for the project's life -> root `CLAUDE.md`, not here.
- Subsystem depth (how the renderer works, what the pipeline costs) -> a project skill under `.claude/skills/`, not here. Skill descriptions sit in context for ~20 tokens each and the body loads only when relevant.

## What earns a place in this file
A rule belongs here only if ALL FOUR hold. Otherwise route it:
1. It applies to ANY change in this project - not one subsystem. (Subsystem -> a skill.)
2. It is not a general engineering or epistemic principle. (General -> `~/.claude/CLAUDE.md`, where it works across every project.)
3. It is not a standing user preference. (Preference -> `~/.claude/CLAUDE.md`.)
4. Breaking it costs real money, real data, or something the user cannot undo.

**Cap 8 KB, measured in bytes, not lines.** A line cap on paragraph-length entries is not a cap - one project's rules file reached 57 KB and 105 rules against a "200 line" limit, and ~70% of it had already been superseded by project skills. One sentence per rule plus a pointer; the long version lives in the skill.

## Status marks
Use these for any step or task that needs a status — in handoff's Active task section and elsewhere:
- `[ ]` todo
- `[~]` in progress
- `[x]` done
- `[!]` blocked

## Populating from empty
- **handoff.md** - Last updated (date + session N) / Current state (3 sentences) / Active task (what, why, remaining steps with status marks and owner) / Open threads (max 5) / Next recommended step / Out of scope. No "changed files" section - `git log` and `git diff` answer that for free and never go stale.
- **backlog.md** - parked items only. Not a session log.

## Quick reference: when to touch what
| Event | handoff.md | rules.md | backlog.md | CLAUDE.md |
|---|---|---|---|---|
| Made a code change | yes | - | - | - |
| Hit a blocker / found a bug | yes | - | - | - |
| Finished task, starting new one | yes | - | - | - |
| Task boundary / ~50% context | yes | - | - | - |
| User says "add a project rule" | - | yes | - | - |
| User says "park that" / "add to backlog" | - | - | yes | - |
| Discovered a permanent gotcha | yes | - | - | only if user agrees |

## Project-specific rules
<!-- Tech stack, code conventions, agent workflow constraints (e.g. "never run git"), security rules - append as discovered. Skip anything guessable from the code. -->
