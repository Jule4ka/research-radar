"""Transparent, metadata-only quality scoring.

A paper that's days old has no citations yet, so we can't rank by impact. We
rank by paper-intrinsic *credibility* signals that exist at birth — the venue,
the document type, scholarly substance and topic-fit — plus open access as a
tie-breaker. This judges how *serious / credible* a paper is, not how good its
ideas are (only reading it can do that).

Ranking is deliberately NOT about who wrote it or which stream matched: streams
decide what *enters* the radar; this score decides what's worth reading within
it. `assess()` returns (score, reason) so the digest can show its working.
"""

from __future__ import annotations

from .config import Stream, LOW_PRIORITY_TOPICS
from .openalex import Paper

LOW_PRIORITY_PENALTY = 50  # keeps a low-priority topic in the digest, out of drafts

# Document types that are never worth a draft.
DROP_TYPES = {
    "editorial", "erratum", "retraction", "paratext", "grant",
    "peer-review", "letter", "reference-entry",
}

OA_BONUS = 5  # open access — a practical tie-breaker, not a quality claim


def _venue(p: Paper) -> tuple[int, str]:
    t = (p.venue_type or "").lower()
    if t == "journal":
        return (40, "📗 peer-reviewed journal (DOAJ)") if p.is_in_doaj else (30, "📗 journal")
    if t == "conference":
        return 30, "📙 conference"
    if t in ("book series", "ebook platform", "book"):
        return 20, "📘 book venue"
    if t == "repository":
        return 10, "📄 preprint / repository"
    return (8, "📄 other venue") if t else (5, "— venue unknown")


def _doctype(p: Paper) -> tuple[int, str]:
    t = (p.type or "").lower()
    if t == "review":
        return 20, "📝 review/survey"
    if t == "article":
        return 15, "📄 research article"
    if t in ("book-chapter", "book"):
        return 10, "📘 book chapter"
    if t == "preprint":
        return 8, "📄 preprint"
    if t == "dataset":
        return 5, "🗂 dataset"
    return 5, f"📄 {t or 'work'}"


def _substance(p: Paper) -> tuple[int, list[str]]:
    pts, notes = 0, []
    if p.refs_count >= 40:
        pts += 15; notes.append(f"📚 {p.refs_count} refs")
    elif p.refs_count >= 20:
        pts += 10; notes.append(f"📚 {p.refs_count} refs")
    elif p.refs_count >= 10:
        pts += 5; notes.append(f"📚 {p.refs_count} refs")
    if p.abstract:
        pts += 5; notes.append("has abstract")
    return pts, notes


def _topic_fit(p: Paper) -> tuple[int, str]:
    if p.topic_score >= 0.8:
        return 10, "🎯 strong topic fit"
    if p.topic_score >= 0.6:
        return 5, "🎯 fair topic fit"
    return 0, ""


def assess(paper: Paper, stream: Stream) -> tuple[int, str]:
    """Return (score, reason). Score < 0 means: drop this paper."""
    if paper.type and paper.type.lower() in DROP_TYPES:
        return -1, f"dropped: document type “{paper.type}”"

    # `require` is kept purely as a noise filter (not a scored signal).
    text = f"{paper.title} {paper.abstract}".lower()
    if stream.require and not any(r.lower() in text for r in stream.require):
        return -1, "dropped: no required phrase present"

    score = 0
    notes: list[str] = []
    for pts, label in (_venue(paper), _doctype(paper), _topic_fit(paper)):
        score += pts
        if label:
            notes.append(label)
    sub_pts, sub_notes = _substance(paper)
    score += sub_pts
    notes += sub_notes
    if paper.is_oa:
        score += OA_BONUS
        notes.append("🔓 open access")

    # De-prioritise "watch only" topics so they stay in the digest but rarely
    # beat higher-priority work for a draft slot.
    if stream.key.startswith("topic_") and stream.key[6:] in LOW_PRIORITY_TOPICS:
        score -= LOW_PRIORITY_PENALTY
        notes.append("↓ lower priority")

    return score, " · ".join(notes)
