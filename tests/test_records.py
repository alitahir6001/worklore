from worklore.records import Context, validate_file, validate_record
from worklore.turns import Turn

SID = "2026-10-14-sync"
CTX = Context(
    turns_by_id={
        f"{SID}#t001": Turn(1, "Jane Smith", "00:00:03", "Marcus will ship the proc by Friday."),
        f"{SID}#t002": Turn(2, "Marcus Lee", "00:00:10", "Yes, I'll do it."),
    },
    speakers_by_source={SID: {"Jane Smith", "Marcus Lee"}},
    kb_ids={"reporting.usp_calc"},
    record_ids={f"{SID}#r01", "2026-09-01-old#r03"},
)


def good(**overrides):
    r = {
        "id": f"{SID}#r01", "type": "action_item", "text": "Marcus ships the proc by Friday.",
        "basis": "canon", "evidence": [f"{SID}#t001", f"{SID}#t002"], "owner": "Marcus Lee",
        "speakers": ["Jane Smith"], "subjects": [{"kind": "kb_object", "ref": "Reporting.usp_Calc"}],
        "observed_at": "2026-10-14",
    }
    r.update(overrides)
    return r


def errors(**overrides):
    return validate_record(good(**overrides), SID, CTX)


def test_valid_record_passes():
    assert errors() == []


def test_requires_evidence_that_exists():
    assert any("at least one turn" in e for e in errors(evidence=[]))
    assert any("does not exist" in e for e in errors(evidence=[f"{SID}#t099"]))


def test_rejects_bad_type_basis_id_and_text():
    assert any("type" in e for e in errors(type="opinion"))
    assert any("basis" in e for e in errors(basis="likely"))
    assert any("id must start" in e for e in errors(id="other#r01"))
    assert any("text is empty" in e for e in errors(text=" "))


def test_owner_must_be_named_in_cited_turns():
    assert any("owner" in e for e in errors(owner="Priya Raman"))
    assert errors(owner="Marcus") == []


def test_unknown_speaker_rejected():
    assert any("does not speak" in e for e in errors(speakers=["Dave"]))


def test_kb_refs_checked_case_insensitively():
    assert errors(subjects=[{"kind": "kb_object", "ref": "REPORTING.USP_CALC"}]) == []
    assert any("not in the KB" in e for e in errors(subjects=[{"kind": "kb_object", "ref": "dbo.nope"}]))


def test_kb_refs_skipped_without_kb():
    no_kb = Context(CTX.turns_by_id, CTX.speakers_by_source, None, CTX.record_ids)
    assert validate_record(good(subjects=[{"kind": "kb_object", "ref": "dbo.nope"}]), SID, no_kb) == []


def test_links_must_point_at_known_records():
    assert errors(supersedes=["2026-09-01-old#r03"]) == []
    assert any("unknown record" in e for e in errors(conflicts_with=["nope#r01"]))


def test_duplicate_ids_rejected():
    assert any("duplicate" in e for e in validate_file([good(), good()], SID, CTX))
