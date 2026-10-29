"""Where Worklore's data lives. Code (this repo) and data never share a folder."""

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def inbox(self) -> Path:
        return self.root / "inbox"

    @property
    def sources(self) -> Path:
        return self.root / "sources"

    @property
    def records(self) -> Path:
        return self.root / "records"

    @property
    def db(self) -> Path:
        return self.root / "lore.db"

    def source(self, source_id: str) -> Path:
        return self.sources / source_id

    def ensure(self) -> "Paths":
        for d in (self.inbox, self.sources, self.records):
            d.mkdir(parents=True, exist_ok=True)
        return self


def data_paths() -> Paths:
    root = Path(os.environ.get("WORKLORE_DATA", "~/worklore-data")).expanduser().resolve()
    # Data inside the repo is one `git add .` away from leaking work content.
    if (REPO_ROOT / "pyproject.toml").exists() and root.is_relative_to(REPO_ROOT):
        raise SystemExit(f"WORKLORE_DATA ({root}) is inside the code repo; move it outside.")
    return Paths(root).ensure()


def kb_path() -> Path | None:
    value = os.environ.get("WORKLORE_KB")
    return Path(value).expanduser().resolve() if value else None
