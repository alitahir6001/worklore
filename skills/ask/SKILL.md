---
name: ask
description: Answer questions about past meetings, decisions, action items, systems, or database objects from the Worklore library, with turn-ID citations. Use when the user asks what was said, decided, or committed, why something is the way it is, what's unresolved, or what to review before a meeting.
---

# ask

## Find
1. Break the question into who / what / when. Pick filters: `--speaker`, `--project`,
   `--since`/`--until`.
2. Search records first: `lore records --q "<keywords>"`, `--type`, or `--subject <ref>`.
3. Then turns: `lore search "<keywords and synonyms>" [filters]`. Run several searches with
   different wording. Search matches any word, best first. With no query and a `--speaker`,
   it lists everything that person said.
4. Read the evidence: `lore turns <turn_id> --context 3` for every turn you'll cite. Don't
   cite a turn you haven't read.
5. For database objects: `lore kb <name>` gives the dependencies and the meeting records
   about the object. When the live DB connection is available (work machine, read-only),
   use it to confirm current definitions. Say which facts came from the live DB.

## Answer
- Every claim cites turn IDs: `... [2026-09-15-kt-customer-bi-pipeline#t006]`.
- Label inferences: "inferred:" for anything you connected yourself, and for records with
  `basis: inferred`.
- Show change over time: when a record shows "superseded by" or "conflicts with", give
  both versions with their dates. Never silently pick one.
- If the library doesn't have it, say "not in the library" and what you searched. Don't
  fill gaps from general knowledge.
- Keep the answer short. Citations carry the detail.
