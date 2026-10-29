import sys
from datetime import date
from pathlib import Path

from worklore.parse_docx import normalize_ts, parse_docx, parse_paragraphs

sys.path.insert(0, str(Path(__file__).parents[1] / "fixtures"))
import make_fixtures  # noqa: E402


def test_normalize_ts():
    assert normalize_ts("0:03") == "00:00:03"
    assert normalize_ts("12:34") == "00:12:34"
    assert normalize_ts("1:02:03") == "01:02:03"


def test_parse_paragraphs_turns_preamble_and_date():
    parsed = parse_paragraphs([
        "Weekly sync", "October 14, 2026, 2:00PM", "",
        "Jane Smith   0:03", "First thing.", "Continued thought.",
        "Bob Jones\t1:02:03", "Reply.",
    ])
    assert parsed.preamble == ["Weekly sync", "October 14, 2026, 2:00PM"]
    assert parsed.date == date(2026, 10, 14)
    assert [(t.seq, t.speaker, t.ts, t.text) for t in parsed.turns] == [
        (1, "Jane Smith", "00:00:03", "First thing. Continued thought."),
        (2, "Bob Jones", "01:02:03", "Reply."),
    ]


def test_single_space_time_in_text_is_not_a_header():
    parsed = parse_paragraphs(["Jane Smith   0:03", "Let's meet at 3:30"])
    assert len(parsed.turns) == 1
    assert parsed.turns[0].text == "Let's meet at 3:30"


def test_header_without_text_is_dropped_and_turns_renumbered():
    parsed = parse_paragraphs(["A B   0:01", "B C   0:02", "hi"])
    assert [(t.seq, t.speaker) for t in parsed.turns] == [(1, "B C")]


def test_abbreviated_and_iso_dates():
    assert parse_paragraphs(["Oct 6, 2026"]).date == date(2026, 10, 6)
    assert parse_paragraphs(["2026-10-06 standup"]).date == date(2026, 10, 6)
    assert parse_paragraphs(["no date here"]).date is None


def test_fixture_docx_roundtrip(tmp_path):
    paths = {p.name: p for p in make_fixtures.write(tmp_path)}
    parsed = parse_docx(paths["kt-customer-bi.docx"])
    assert parsed.date == date(2026, 9, 15)
    assert len(parsed.turns) == 11
    assert "reads the snapshot now" in parsed.turns[5].text  # two paragraphs joined
