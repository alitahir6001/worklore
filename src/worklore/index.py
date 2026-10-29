"""Build lore.db from the files. The DB is derived: delete it and `lore index` rebuilds it."""

import json
import sqlite3

from . import records as rec
from . import turns as tn
from .config import Paths
from .kb import FixtureKB

SCHEMA = """
create table sources(id text primary key, title text, date text, project text, cleaned int);
create table turns(id text primary key, source_id text, seq int, speaker text, ts text,
                   text text, raw_text text);
create virtual table turns_fts using fts5(turn_id unindexed, text);
create table records(id text primary key, source_id text, type text, text text, basis text,
                     owner text, due text, status text, observed_at text, body text);
create virtual table records_fts using fts5(record_id unindexed, text);
create table record_subjects(record_id text, kind text, ref text);
create table record_evidence(record_id text, turn_id text);
create table record_links(record_id text, rel text, ref text);
"""


def load_library(paths: Paths, kb: FixtureKB | None):
    """Read every source and record file. Returns (sources, ctx, records_by_source, file_errors)."""
    sources = []
    ctx = rec.Context({}, {}, kb.ids() if kb else None)
    for src_dir in sorted(p for p in paths.sources.iterdir() if (p / "meta.json").exists()):
        meta = json.loads((src_dir / "meta.json").read_text())
        raw, _ = tn.parse((src_dir / "turns.raw.md").read_text())
        clean_path = src_dir / "turns.clean.md"
        clean, clean_errors = None, []
        if clean_path.exists():
            clean, malformed = tn.parse(clean_path.read_text())
            clean_errors = tn.validate_clean(raw, clean, malformed)
        sources.append((meta, raw, clean, clean_errors))
        ctx.speakers_by_source[meta["id"]] = {t.speaker for t in raw}
        for t in raw:
            ctx.turns_by_id[tn.turn_id(meta["id"], t.seq)] = t

    records_by_source, file_errors = {}, {}
    for path in sorted(paths.records.glob("*.jsonl")):
        records, errors = rec.load(path)
        records_by_source[path.stem] = records
        file_errors[path.stem] = errors
        ctx.record_ids.update(r.get("id") for r in records)
    return sources, ctx, records_by_source, file_errors


def build(paths: Paths, kb: FixtureKB | None) -> dict:
    sources, ctx, records_by_source, _ = load_library(paths, kb)
    tmp = paths.db.with_suffix(".db.tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    warnings = []

    for meta, raw, clean, clean_errors in sources:
        sid = meta["id"]
        # Only trust cleaned text when it lines up turn-for-turn with raw.
        use_clean = clean is not None and not clean_errors
        if clean is not None and clean_errors:
            warnings.append(f"{sid}: cleaned transcript fails validation; indexed raw text")
        con.execute("insert into sources values (?,?,?,?,?)",
                    (sid, meta["title"], meta["date"], meta["project"], int(use_clean)))
        for i, t in enumerate(raw):
            tid = tn.turn_id(sid, t.seq)
            text = clean[i].text if use_clean else t.text
            con.execute("insert into turns values (?,?,?,?,?,?,?)",
                        (tid, sid, t.seq, t.speaker, t.ts, text, t.text))
            con.execute("insert into turns_fts values (?,?)", (tid, text))

    skipped = 0
    for sid, records in records_by_source.items():
        for r in records:
            if errs := rec.validate_record(r, sid, ctx):
                skipped += 1
                warnings.extend(errs)
                continue
            rid = r["id"]
            con.execute("insert into records values (?,?,?,?,?,?,?,?,?,?)",
                        (rid, sid, r["type"], r["text"], r["basis"], r.get("owner"), r.get("due"),
                         r.get("status"), r.get("observed_at"), json.dumps(r)))
            con.execute("insert into records_fts values (?,?)", (rid, r["text"]))
            con.executemany("insert into record_subjects values (?,?,?)",
                            [(rid, s["kind"], s["ref"]) for s in r.get("subjects") or []])
            con.executemany("insert into record_evidence values (?,?)",
                            [(rid, t) for t in r["evidence"]])
            con.executemany("insert into record_links values (?,?,?)",
                            [(rid, key, ref) for key in rec.LINK_KEYS for ref in r.get(key) or []])

    counts = {t: con.execute(f"select count(*) from {t}").fetchone()[0]
              for t in ("sources", "turns", "records")}
    con.commit()
    con.close()
    tmp.replace(paths.db)
    counts["skipped_records"] = skipped
    counts["warnings"] = warnings
    return counts
