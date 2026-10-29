"""Read-only view of the database-audit KB.

FixtureKB reads the stand-in layout in fixtures/kb (objects.jsonl + edges.jsonl). The real
adapter gets written against the kb-survey report and must keep the same methods.
"""

import json
from pathlib import Path


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


class FixtureKB:
    def __init__(self, root: Path):
        self.root = root
        self._objects = {o["id"].lower(): o for o in _jsonl(root / "objects.jsonl")}
        self._edges = _jsonl(root / "edges.jsonl")

    def ids(self) -> set[str]:
        return set(self._objects)

    def get(self, ref: str) -> dict | None:
        return self._objects.get(ref.lower())

    def find(self, fragment: str) -> list[str]:
        frag = fragment.lower()
        return sorted(o["id"] for k, o in self._objects.items() if frag in k)

    def edges_of(self, ref: str) -> tuple[list[dict], list[dict]]:
        """(edges where ref is the user, edges where ref is used)."""
        key = ref.lower()
        uses = [e for e in self._edges if e["from"].lower() == key]
        used_by = [e for e in self._edges if e["to"].lower() == key]
        return uses, used_by


def load_kb(path: Path | None) -> FixtureKB | None:
    return FixtureKB(path) if path else None
