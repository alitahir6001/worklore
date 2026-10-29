"""`lore`: the only way agents (and you) read and write the library."""

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

from . import index as ix
from . import records as rec
from . import turns as tn
from .config import Paths, data_paths, kb_path
from .kb import load_kb
from .parse_docx import parse_docx


def _content_hash(parsed) -> str:
    # Hash the turns, not the file bytes: re-exporting the same transcript changes the bytes.
    body = "\n".join(f"{t.speaker}|{t.ts}|{t.text}" for t in parsed.turns)
    return hashlib.sha256(body.encode()).hexdigest()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50] or "untitled"


def _metas(paths: Paths) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(paths.sources.glob("*/meta.json"))]


def _db(paths: Paths) -> sqlite3.Connection:
    if not paths.db.exists():
        sys.exit("No index yet: run `lore index`.")
    con = sqlite3.connect(paths.db)
    con.row_factory = sqlite3.Row
    return con


def _fts_query(text: str) -> str:
    # OR of quoted tokens: punctuation-safe, and bm25 ranks the best matches first.
    return " OR ".join(f'"{t}"' for t in re.findall(r"\w+", text))


def cmd_status(args, paths: Paths) -> int:
    metas = _metas(paths)
    known = {m["content_sha256"] for m in metas}
    print(f"data:  {paths.root}")
    print(f"kb:    {kb_path() or 'not set (WORKLORE_KB)'}")
    inbox = sorted(p for p in paths.inbox.iterdir() if p.suffix.lower() == ".docx")
    print(f"inbox: {len(inbox)} file(s)")
    for p in inbox:
        print(f"  {p.name}{'  (already ingested)' if _content_hash(parse_docx(p)) in known else ''}")
    uncleaned = [m["id"] for m in metas if not (paths.source(m["id"]) / "turns.clean.md").exists()]
    unextracted = [m["id"] for m in metas if not (paths.records / f"{m['id']}.jsonl").exists()]
    print(f"sources: {len(metas)}  (needs cleaning: {len(uncleaned)}, needs records: {len(unextracted)})")
    for sid in uncleaned:
        print(f"  needs cleaning: {sid}")
    for sid in unextracted:
        print(f"  needs records:  {sid}")
    files = list(paths.sources.rglob("*")) + list(paths.records.glob("*.jsonl"))
    newest = max((f.stat().st_mtime for f in files if f.is_file()), default=0)
    if not paths.db.exists():
        print("index: missing (run `lore index`)")
    else:
        print("index: stale (run `lore index`)" if paths.db.stat().st_mtime < newest else "index: up to date")
    return 0


def cmd_peek(args, paths: Paths) -> int:
    parsed = parse_docx(args.docx)
    print(f"date (parsed): {parsed.date or 'not found; pass --date to parse'}")
    print("preamble:")
    for line in parsed.preamble:
        print(f"  {line}")
    speakers: dict[str, int] = {}
    for t in parsed.turns:
        speakers[t.speaker] = speakers.get(t.speaker, 0) + 1
    print(f"turns: {len(parsed.turns)}  speakers: " + ", ".join(f"{s} ({n})" for s, n in speakers.items()))
    for t in parsed.turns[: args.turns]:
        print(f"  [{tn.tag(t.seq)}] {t.speaker} ({t.ts}): {t.text[:200]}")
    return 0


def cmd_parse(args, paths: Paths) -> int:
    docx = args.docx.resolve()
    parsed = parse_docx(docx)
    if not parsed.turns:
        sys.exit("No speaker turns found: the docx layout doesn't match parse_docx.HEADER.")
    sha = _content_hash(parsed)
    if dup := next((m["id"] for m in _metas(paths) if m["content_sha256"] == sha), None):
        sys.exit(f"Already ingested as {dup}.")
    day = args.date or parsed.date
    if not day:
        sys.exit("No date found in the transcript: pass --date YYYY-MM-DD.")
    title = args.title or (parsed.preamble[0] if parsed.preamble else docx.stem)
    base = f"{day.isoformat()}-{_slug(title)}"
    sid, n = base, 2
    while paths.source(sid).exists():
        sid, n = f"{base}-{n}", n + 1

    src = paths.source(sid)
    src.mkdir(parents=True)
    shutil.copy2(docx, src / "raw.docx")
    meta = {
        "id": sid, "title": title, "date": day.isoformat(), "project": args.project,
        "content_sha256": sha, "original_name": docx.name, "preamble": parsed.preamble,
        "parsed_at": datetime.now().isoformat(timespec="seconds"),
    }
    (src / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    (src / "turns.raw.md").write_text(tn.render(meta, parsed.turns))
    if docx.parent == paths.inbox.resolve():
        docx.unlink()  # the original is preserved as raw.docx
    print(f"{sid}: {len(parsed.turns)} turns -> {src / 'turns.raw.md'}")
    print(f"next: write {src / 'turns.clean.md'} (clean-transcript skill), then `lore validate {sid}`")
    return 0


def cmd_validate(args, paths: Paths) -> int:
    sources, ctx, records_by_source, file_errors = ix.load_library(paths, load_kb(kb_path()))
    wanted = set(args.source_ids)
    failed = False
    for meta, _raw, clean, clean_errors in sources:
        sid = meta["id"]
        if wanted and sid not in wanted:
            continue
        problems = list(clean_errors)
        if sid in records_by_source:
            problems += file_errors[sid] + rec.validate_file(records_by_source[sid], sid, ctx)
        state = []
        state.append("cleaned" if clean is not None else "not cleaned")
        state.append(f"{len(records_by_source[sid])} records" if sid in records_by_source else "no records")
        print(f"{sid}: {', '.join(state)}: {'OK' if not problems else f'{len(problems)} problem(s)'}")
        for p in problems[:20]:
            print(f"  - {p}")
        failed |= bool(problems)
    return 1 if failed else 0


def cmd_index(args, paths: Paths) -> int:
    counts = ix.build(paths, load_kb(kb_path()))
    print(f"indexed {counts['sources']} sources, {counts['turns']} turns, {counts['records']} records"
          f" ({counts['skipped_records']} invalid records skipped)")
    for w in counts["warnings"][:20]:
        print(f"  ! {w}")
    return 0


def _filters(args, clauses: list[str], params: list) -> None:
    if args.project:
        clauses.append("s.project = ?")
        params.append(args.project)
    if args.since:
        clauses.append("s.date >= ?")
        params.append(args.since.isoformat())
    if args.until:
        clauses.append("s.date <= ?")
        params.append(args.until.isoformat())


def cmd_search(args, paths: Paths) -> int:
    con = _db(paths)
    clauses, params = [], []
    query = _fts_query(args.query or "")
    if query:
        sql = ("select t.*, s.date, s.project from turns_fts f join turns t on t.id = f.turn_id "
               "join sources s on s.id = t.source_id where turns_fts match ?")
        params.append(query)
        order = "bm25(turns_fts)"
    else:
        sql = "select t.*, s.date, s.project from turns t join sources s on s.id = t.source_id where 1=1"
        order = "s.date, t.source_id, t.seq"
    if args.speaker:
        clauses.append("t.speaker like ?")
        params.append(f"%{args.speaker}%")
    _filters(args, clauses, params)
    sql += "".join(f" and {c}" for c in clauses) + f" order by {order} limit ?"
    rows = con.execute(sql, params + [args.limit]).fetchall()
    for r in rows:
        print(f"{r['id']} | {r['date']} | {r['project']} | {r['speaker']} {r['ts']} | {r['text']}")
    print(f"({len(rows)} turn(s){'; raise --limit for more' if len(rows) == args.limit else ''})")
    return 0


def cmd_records(args, paths: Paths) -> int:
    con = _db(paths)
    sql = "select r.*, s.project from records r join sources s on s.id = r.source_id where 1=1"
    clauses, params = [], []
    if args.subject:
        clauses.append("r.id in (select record_id from record_subjects where lower(ref) = lower(?))")
        params.append(args.subject)
    if args.type:
        clauses.append("r.type = ?")
        params.append(args.type)
    if args.q and (query := _fts_query(args.q)):
        clauses.append("r.id in (select record_id from records_fts where records_fts match ?)")
        params.append(query)
    _filters(args, clauses, params)
    sql += "".join(f" and {c}" for c in clauses) + " order by r.observed_at, r.id limit ?"
    rows = con.execute(sql, params + [args.limit]).fetchall()
    for r in rows:
        body = json.loads(r["body"])
        print(f"{r['id']} [{r['type']}, {r['basis']}] {r['observed_at'] or ''} {r['project']}")
        print(f"  {r['text']}")
        extras = [f"{k}: {body[k]}" for k in ("owner", "due", "status") if body.get(k)]
        if extras:
            print(f"  {'  '.join(extras)}")
        if body.get("subjects"):
            print("  subjects: " + ", ".join(f"{s['kind']}:{s['ref']}" for s in body["subjects"]))
        print("  evidence: " + ", ".join(body["evidence"]))
        for key in rec.LINK_KEYS:
            if body.get(key):
                print(f"  {key}: {', '.join(body[key])}")
        for link in con.execute("select record_id, rel from record_links where ref = ?", (r["id"],)):
            print(f"  ! {'superseded by' if link['rel'] == 'supersedes' else 'conflicts with'} {link['record_id']}")
    print(f"({len(rows)} record(s))")
    return 0


def cmd_turns(args, paths: Paths) -> int:
    con = _db(paths)
    source_id, seq = tn.split_turn_id(args.turn_id)
    src = con.execute("select * from sources where id = ?", (source_id,)).fetchone()
    if not src:
        sys.exit(f"Unknown source {source_id}.")
    print(f"{src['title']} | {src['date']} | {src['project']}{'' if src['cleaned'] else ' | (raw text)'}")
    rows = con.execute("select * from turns where source_id = ? and seq between ? and ? order by seq",
                       (source_id, seq - args.context, seq + args.context)).fetchall()
    if not any(r["seq"] == seq for r in rows):
        sys.exit(f"Unknown turn {args.turn_id}.")
    for r in rows:
        mark = ">" if r["seq"] == seq else " "
        print(f"{mark} [{tn.tag(r['seq'])}] {r['speaker']} ({r['ts']}): {r['raw_text'] if args.raw else r['text']}")
    return 0


def cmd_kb(args, paths: Paths) -> int:
    kb = load_kb(kb_path())
    if not kb:
        sys.exit("No KB configured: set WORKLORE_KB.")
    obj = kb.get(args.ref)
    if not obj:
        matches = kb.find(args.ref)
        print(f"No exact match for {args.ref!r}." + (" Did you mean:" if matches else ""))
        for m in matches[:20]:
            print(f"  {m}")
        return 1
    print(json.dumps(obj, indent=2))
    uses, used_by = kb.edges_of(obj["id"])
    print("uses:")
    for e in uses:
        print(f"  {e['type']} {e['to']}{'  (dynamic SQL)' if e.get('dynamic') else ''}")
    print("used by:")
    for e in used_by:
        print(f"  {e['from']} {e['type']} it{'  (dynamic SQL)' if e.get('dynamic') else ''}")
    if paths.db.exists():
        con = _db(paths)
        rows = con.execute("select r.id, r.type, r.text from records r join record_subjects rs "
                           "on rs.record_id = r.id where lower(rs.ref) = lower(?) order by r.observed_at",
                           (obj["id"],)).fetchall()
        print(f"meeting records: {len(rows)}")
        for r in rows:
            print(f"  {r['id']} [{r['type']}] {r['text']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="lore", description="Lore & Order: query your work meetings.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="inbox, pipeline stage per source, index freshness")

    s = sub.add_parser("peek", help="preview a transcript without ingesting it")
    s.add_argument("docx", type=Path)
    s.add_argument("--turns", type=int, default=12)

    s = sub.add_parser("parse", help="ingest a .docx into the library as turn-tagged markdown")
    s.add_argument("docx", type=Path)
    s.add_argument("--project", required=True)
    s.add_argument("--title")
    s.add_argument("--date", type=date.fromisoformat)

    s = sub.add_parser("validate", help="check cleaned transcripts and records against the raw turns")
    s.add_argument("source_ids", nargs="*")

    sub.add_parser("index", help="rebuild lore.db from the files")

    def add_filters(s):
        s.add_argument("--project")
        s.add_argument("--since", type=date.fromisoformat)
        s.add_argument("--until", type=date.fromisoformat)
        s.add_argument("--limit", type=int, default=20)

    s = sub.add_parser("search", help="keyword search over turns (any word matches; best first)")
    s.add_argument("query", nargs="?")
    s.add_argument("--speaker")
    add_filters(s)

    s = sub.add_parser("records", help="list extracted records")
    s.add_argument("--subject", help="exact subject ref, e.g. a KB object ID")
    s.add_argument("--type", choices=sorted(rec.TYPES))
    s.add_argument("--q", help="keywords in the record text")
    add_filters(s)

    s = sub.add_parser("turns", help="show a turn with surrounding context")
    s.add_argument("turn_id")
    s.add_argument("--context", type=int, default=2)
    s.add_argument("--raw", action="store_true", help="show the uncleaned text")

    s = sub.add_parser("kb", help="look up a KB object, its dependencies, and meeting records about it")
    s.add_argument("ref")

    args = p.parse_args(argv)
    handler = globals()[f"cmd_{args.cmd}"]
    return handler(args, data_paths())


if __name__ == "__main__":
    sys.exit(main())
