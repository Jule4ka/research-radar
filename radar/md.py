"""Tiny shared helpers for formatting a Paper into Markdown.

Used by both report renderers (deliver.py and canon.py) so neither has to reach
into the other's internals.
"""

from __future__ import annotations

from .openalex import Paper


def cell(text: str) -> str:
    """Make a string safe to drop into a Markdown table cell."""
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def authors(p: Paper, n: int = 3) -> str:
    shown = ", ".join(p.authors[:n])
    return shown + (" et al." if len(p.authors) > n else "")


def access(p: Paper) -> str:
    label = f"🔓 {p.oa_status or 'open'}" if p.is_oa else "🔒 closed"
    if p.local_path:
        label += f" · [📥 saved]({p.local_path})"
    return label


def doi(p: Paper) -> str:
    return f"[{cell(p.doi)}]({p.doi_url})" if p.doi else "—"
