"""Extracted knowledge records, and the checks that keep every record tied to its evidence."""

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .turns import Turn

TYPES = {"decision", "action_item", "fact", "open_question"}
BASES = {"canon", "inferred"}
SUBJECT_KINDS = {"kb_object", "project", "system"}
LINK_KEYS = ("supersedes", "conflicts_with")


@dataclass
class Context:
    turns_by_id: dict[str, Turn]
    speakers_by_source: dict[str, set[str]]
    kb_ids: set[str] | None  # lowercased; None = no KB configured, skip ref checks
    record_ids: set[str] = field(default_factory=set)


def load(path: Path) -> tuple[list[dict], list[str]]:
    records, errors = [], []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            errors.append(f"line {n}: invalid JSON ({e.msg})")
    return records, errors


def validate_record(r: dict, source_id: str, ctx: Context) -> list[str]:
    rid = r.get("id", "<no id>")
    errs = []

    def bad(msg: str) -> None:
        errs.append(f"{rid}: {msg}")

    if not str(rid).startswith(f"{source_id}#r"):
        bad(f"id must start with {source_id}#r")
    if r.get("type") not in TYPES:
        bad(f"type must be one of {sorted(TYPES)}")
    if not str(r.get("text", "")).strip():
        bad("text is empty")
    if r.get("basis") not in BASES:
        bad("basis must be 'canon' (stated in the cited turns) or 'inferred'")

    evidence = r.get("evidence") or []
    if not evidence:
        bad("evidence must cite at least one turn ID")
    cited = [ctx.turns_by_id[t] for t in evidence if t in ctx.turns_by_id]
    for t in evidence:
        if t not in ctx.turns_by_id:
            bad(f"evidence turn {t} does not exist")

    known_speakers = ctx.speakers_by_source.get(source_id, set())
    for s in r.get("speakers") or []:
        if s not in known_speakers:
            bad(f"speaker {s!r} does not speak in {source_id}")

    if owner := r.get("owner"):
        haystack = " ".join(f"{t.speaker} {t.text}" for t in cited).lower()
        if not any(part in haystack for part in owner.lower().split() if len(part) > 2):
            bad(f"owner {owner!r} is not named in the cited turns")

    if observed := r.get("observed_at"):
        try:
            date.fromisoformat(observed)
        except ValueError:
            bad("observed_at must be YYYY-MM-DD")

    for s in r.get("subjects") or []:
        if s.get("kind") not in SUBJECT_KINDS or not s.get("ref"):
            bad(f"subject {s} needs kind in {sorted(SUBJECT_KINDS)} and a ref")
        elif s["kind"] == "kb_object" and ctx.kb_ids is not None and s["ref"].lower() not in ctx.kb_ids:
            bad(f"kb_object {s['ref']!r} is not in the KB (find the exact ID with `lore kb`)")

    for key in LINK_KEYS:
        for ref in r.get(key) or []:
            if ref not in ctx.record_ids:
                bad(f"{key} points at unknown record {ref}")
    return errs


def validate_file(records: list[dict], source_id: str, ctx: Context) -> list[str]:
    errs = []
    seen = set()
    for r in records:
        if r.get("id") in seen:
            errs.append(f"{r.get('id')}: duplicate id")
        seen.add(r.get("id"))
        errs.extend(validate_record(r, source_id, ctx))
    return errs
