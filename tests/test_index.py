import json
import sqlite3
from pathlib import Path

from worklore import index as ix
from worklore.config import Paths
from worklore.kb import FixtureKB
from worklore.turns import Turn, render

KB = FixtureKB(Path(__file__).parents[1] / "fixtures" / "kb")
SID = "2026-09-15-kt"


def library(tmp_path, clean_texts=None, records=()):
    paths = Paths(tmp_path).ensure()
    meta = {"id": SID, "title": "KT", "date": "2026-09-15", "project": "bi", "sha256": "x"}
    raw = [Turn(1, "Priya Raman", "00:00:12", "Um, it's in usp_CalcCustomerBI."),
           Turn(2, "Sam Rivera", "00:00:35", "Uh, what calls it?")]
    src = paths.source(SID)
    src.mkdir()
    (src / "meta.json").write_text(json.dumps(meta))
    (src / "turns.raw.md").write_text(render(meta, raw))
    if clean_texts:
        clean = [Turn(t.seq, t.speaker, t.ts, x) for t, x in zip(raw, clean_texts)]
        (src / "turns.clean.md").write_text(render(meta, clean))
    (paths.records / f"{SID}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    return paths


RECORD = {"id": f"{SID}#r01", "type": "fact", "text": "BI is calculated in usp_CalcCustomerBI.",
          "basis": "canon", "evidence": [f"{SID}#t001"],
          "subjects": [{"kind": "kb_object", "ref": "Reporting.usp_CalcCustomerBI"}]}


def test_build_indexes_clean_text_and_valid_records(tmp_path):
    paths = library(tmp_path, ["It's in usp_CalcCustomerBI.", "What calls it?"],
                    [RECORD, {**RECORD, "id": f"{SID}#r02", "evidence": []}])
    counts = ix.build(paths, KB)
    assert (counts["sources"], counts["turns"], counts["records"], counts["skipped_records"]) == (1, 2, 1, 1)
    con = sqlite3.connect(paths.db)
    text, raw = con.execute("select text, raw_text from turns where id = ?", (f"{SID}#t001",)).fetchone()
    assert text == "It's in usp_CalcCustomerBI." and raw.startswith("Um")
    hits = con.execute("select turn_id from turns_fts where turns_fts match '\"usp_CalcCustomerBI\"'").fetchall()
    assert hits == [(f"{SID}#t001",)]
    assert con.execute("select ref from record_subjects").fetchall() == [("Reporting.usp_CalcCustomerBI",)]


def test_invalid_cleanup_falls_back_to_raw(tmp_path):
    paths = library(tmp_path, ["Merged into one."])
    counts = ix.build(paths, KB)
    assert any("fails validation" in w for w in counts["warnings"])
    con = sqlite3.connect(paths.db)
    assert con.execute("select cleaned from sources").fetchone() == (0,)


def test_rebuild_is_reproducible(tmp_path):
    paths = library(tmp_path, records=[RECORD])
    first = ix.build(paths, KB)
    paths.db.unlink()
    assert ix.build(paths, KB) == first
