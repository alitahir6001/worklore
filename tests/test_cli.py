import sys
from pathlib import Path

import pytest
from docx import Document

from worklore.cli import main

sys.path.insert(0, str(Path(__file__).parents[1] / "fixtures"))
import make_fixtures  # noqa: E402


def test_reexported_transcript_is_not_ingested_twice(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("WORKLORE_DATA", str(tmp_path / "data"))
    first = make_fixtures.write(tmp_path / "a")[0]
    again = make_fixtures.write(tmp_path / "b")[0]
    doc = Document(str(again))
    doc.core_properties.author = "re-export"  # same turns, different file bytes
    doc.save(str(again))
    assert first.read_bytes() != again.read_bytes()

    assert main(["parse", str(first), "--project", "p"]) == 0
    with pytest.raises(SystemExit, match="Already ingested as 2026-09-08-chatbot-requirements-sync"):
        main(["parse", str(again), "--project", "p"])


def test_parse_moves_inbox_file_and_preserves_original(tmp_path, monkeypatch):
    data = tmp_path / "data"
    monkeypatch.setenv("WORKLORE_DATA", str(data))
    main(["status"])  # creates the folders
    docx = make_fixtures.write(data / "inbox")[0]
    assert main(["parse", str(docx), "--project", "p"]) == 0
    assert not docx.exists()
    assert (data / "sources" / "2026-09-08-chatbot-requirements-sync" / "raw.docx").exists()
