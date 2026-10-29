"""Turn-tagged markdown, the shared format for raw and cleaned transcripts.

One turn per line: `[t042] Speaker Name (00:03:12): text`. Global turn ID: `<source_id>#t042`.
"""

import re
from dataclasses import dataclass

LINE = re.compile(r"^\[t(?P<n>\d+)\] (?P<speaker>.+?) \((?P<ts>\d{2}:\d{2}:\d{2})\): (?P<text>.*)$")


@dataclass
class Turn:
    seq: int
    speaker: str
    ts: str  # HH:MM:SS
    text: str


def tag(seq: int) -> str:
    return f"t{seq:03d}"


def turn_id(source_id: str, seq: int) -> str:
    return f"{source_id}#{tag(seq)}"


def split_turn_id(tid: str) -> tuple[str, int]:
    source_id, sep, n = tid.rpartition("#t")
    if not sep or not n.isdigit():
        raise ValueError(f"not a turn ID: {tid!r} (expected <source_id>#tNNN)")
    return source_id, int(n)


def render(meta: dict, turns: list[Turn]) -> str:
    header = [
        f"# {meta['title']}",
        f"source: {meta['id']}",
        f"date: {meta['date']}",
        f"project: {meta['project']}",
        "",
    ]
    body = [f"[{tag(t.seq)}] {t.speaker} ({t.ts}): {t.text}" for t in turns]
    return "\n".join(header + body) + "\n"


def parse(md: str) -> tuple[list[Turn], list[str]]:
    """Return (turns, malformed lines). After the first turn, every non-blank line must be a turn."""
    turns: list[Turn] = []
    malformed: list[str] = []
    for line in md.splitlines():
        m = LINE.match(line)
        if m:
            turns.append(Turn(int(m["n"]), m["speaker"], m["ts"], m["text"].strip()))
        elif line.strip() and (turns or line.startswith("[t")):
            malformed.append(line)
    return turns, malformed


def validate_clean(raw: list[Turn], clean: list[Turn], malformed: list[str]) -> list[str]:
    """Cleanup may rewrite text only; turn count, order, speakers and timestamps must match raw."""
    errors = [f"malformed line (one turn per line, tag kept): {line[:80]!r}" for line in malformed]
    if len(raw) != len(clean):
        errors.append(f"turn count differs: raw {len(raw)}, clean {len(clean)}")
    for r, c in zip(raw, clean):
        where = f"{tag(r.seq)}"
        if r.seq != c.seq:
            errors.append(f"{where}: clean has {tag(c.seq)} here (turns merged, dropped or reordered)")
            break  # everything after a shift would be noise
        if r.speaker != c.speaker:
            errors.append(f"{where}: speaker changed {r.speaker!r} -> {c.speaker!r}")
        if r.ts != c.ts:
            errors.append(f"{where}: timestamp changed {r.ts} -> {c.ts}")
        if r.text and not c.text:
            errors.append(f"{where}: text emptied")
    return errors
