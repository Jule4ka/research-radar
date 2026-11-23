"""Render the run's findings into a Markdown review doc.

The workflow turns this Markdown into a GitHub Issue (via `gh issue create
--body-file`). Running locally, it just writes a file you can open.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from .openalex import Paper

OUT = Path(__file__).resolve().parent.parent / "state" / "latest_report.md"


def render(drafts: list[tuple[Paper, str]], digest: list[Paper]) -> str:
    today = date.today().isoformat()
    lines: list[str] = [f"# Research Radar — {today}", ""]

    if not drafts and not digest:
        lines.append("_No new papers this run._")
        return "\n".join(lines)

    lines.append(f"**{len(drafts)} draft(s) ready to post** · "
                 f"{len(digest)} more new paper(s) in the digest below.")
    lines.append("")

    for i, (paper, text) in enumerate(drafts, 1):
        lines += [
            f"## ✍️ Draft {i} — _{paper.stream}_",
            "",
            "```",
            text,
            "```",
            "",
            f"<sub>{paper.venue} · {paper.date} · "
            f"{paper.url}</sub>",
            "",
            "---",
            "",
        ]

    if digest:
        lines += ["## \U0001F4F0 Also new (digest)", ""]
        for p in digest:
            authors = ", ".join(p.authors[:2]) + (" et al." if len(p.authors) > 2 else "")
            lines.append(f"- **[{p.stream}]** [{p.title}]({p.url}) "
                         f"— {authors}, {p.date}")
        lines.append("")

    lines += ["---", "_Paste the drafts you like into LinkedIn, then close this issue._"]
    return "\n".join(lines)


def write_file(markdown: str) -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(markdown, encoding="utf-8")
    return OUT
