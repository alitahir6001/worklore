import pytest

from worklore.turns import Turn, parse, render, split_turn_id, turn_id, validate_clean

META = {"id": "2026-10-14-sync", "title": "Sync", "date": "2026-10-14", "project": "p"}
RAW = [Turn(1, "Jane Smith", "00:00:03", "Um, so, first thing."), Turn(2, "Bob Jones", "00:01:00", "Uh, yes.")]


def clean_md(texts, turns=RAW):
    return render(META, [Turn(t.seq, t.speaker, t.ts, x) for t, x in zip(turns, texts)])


def test_turn_id_roundtrip():
    assert turn_id("2026-10-14-sync", 42) == "2026-10-14-sync#t042"
    assert split_turn_id("2026-10-14-sync#t042") == ("2026-10-14-sync", 42)
    assert split_turn_id("a#b#t1000") == ("a#b", 1000)
    with pytest.raises(ValueError):
        split_turn_id("2026-10-14-sync")


def test_render_parse_roundtrip():
    turns, malformed = parse(render(META, RAW))
    assert turns == RAW
    assert malformed == []


def test_valid_cleanup_passes():
    clean, malformed = parse(clean_md(["First thing.", "Yes."]))
    assert validate_clean(RAW, clean, malformed) == []


def test_merged_turns_rejected():
    md = render(META, [Turn(1, "Jane Smith", "00:00:03", "First thing. Yes.")])
    clean, malformed = parse(md)
    errors = validate_clean(RAW, clean, malformed)
    assert any("turn count" in e for e in errors)


def test_reordered_turns_rejected():
    md = render(META, [RAW[1], RAW[0]])
    clean, malformed = parse(md)
    assert any("merged, dropped or reordered" in e for e in validate_clean(RAW, clean, malformed))


def test_speaker_timestamp_and_empty_text_rejected():
    md = render(META, [Turn(1, "Jane", "00:00:04", ""), RAW[1]])
    clean, malformed = parse(md)
    errors = validate_clean(RAW, clean, malformed)
    assert any("speaker changed" in e for e in errors)
    assert any("timestamp changed" in e for e in errors)
    assert any("text emptied" in e for e in errors)


def test_turn_split_across_lines_rejected():
    md = clean_md(["First thing.", "Yes."]).replace("First thing.", "First\nthing.")
    clean, malformed = parse(md)
    assert malformed == ["thing."]
    assert validate_clean(RAW, clean, malformed)
