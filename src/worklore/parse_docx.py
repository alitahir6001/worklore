"""Copilot transcript .docx -> speaker turns.

Layout ASSUMPTION until the kb-survey report confirms it: optional preamble (title, date),
then turns made of a header paragraph `<speaker><tab or 2+ spaces><timestamp>` followed by
one or more text paragraphs. Fix HEADER here, nowhere else, when the real layout differs.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .turns import Turn

HEADER = re.compile(r"^(?P<speaker>\S[^\t]*?)(?:\t+|\s{2,})(?P<ts>\d{1,2}:\d{2}(?::\d{2})?)(?:\.\d+)?$")

DATE_PATTERNS = [
    (r"\d{4}-\d{2}-\d{2}", ["%Y-%m-%d"]),
    (r"[A-Z][a-z]+ \d{1,2}, \d{4}", ["%B %d, %Y", "%b %d, %Y"]),
    (r"\d{1,2}/\d{1,2}/\d{4}", ["%m/%d/%Y"]),
]


@dataclass
class Parsed:
    preamble: list[str]
    turns: list[Turn]
    date: date | None


def normalize_ts(ts: str) -> str:
    parts = [int(p) for p in ts.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return f"{h:02d}:{m:02d}:{s:02d}"


def find_date(lines: list[str]) -> date | None:
    for line in lines:
        for pattern, formats in DATE_PATTERNS:
            if not (m := re.search(pattern, line)):
                continue
            for fmt in formats:
                try:
                    return datetime.strptime(m.group(), fmt).date()
                except ValueError:
                    pass
    return None


def parse_paragraphs(paragraphs: list[str]) -> Parsed:
    preamble: list[str] = []
    turns: list[Turn] = []
    for raw in paragraphs:
        line = raw.strip()
        if not line:
            continue
        if m := HEADER.match(line):
            turns.append(Turn(0, m["speaker"].strip(), normalize_ts(m["ts"]), ""))
        elif turns:
            turns[-1].text = f"{turns[-1].text} {line}".strip()
        else:
            preamble.append(line)
    turns = [t for t in turns if t.text]
    for i, t in enumerate(turns, 1):
        t.seq = i
    return Parsed(preamble, turns, find_date(preamble))


def parse_docx(path: Path) -> Parsed:
    from docx import Document

    return parse_paragraphs([p.text for p in Document(str(path)).paragraphs])
