"""Dedupe store: remember which OpenAlex work ids we've already reported.

Backed by a single JSON file (state/seen.json) committed to the repo, so the
GitHub Actions run has an audit trail and never re-reports the same paper.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "state" / "seen.json"


class SeenStore:
    def __init__(self, path: Path = DEFAULT_PATH):
        self.path = path
        self._seen: dict[str, str] = {}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8") or "{}")
            self._seen = data.get("seen", {})

    def is_new(self, short_id: str) -> bool:
        return short_id not in self._seen

    def mark(self, short_id: str) -> None:
        self._seen[short_id] = date.today().isoformat()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated": date.today().isoformat(), "seen": self._seen}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
