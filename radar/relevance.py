"""Cheap relevance scoring to cut noise before drafting.

Score = count of distinct `boost` keywords present in title+abstract, +1 if the
title itself matches a boost term (title hits weigh more). Streams with a
`require` list drop papers that contain none of the required phrases.
"""

from __future__ import annotations

from .config import Stream
from .openalex import Paper


def score(paper: Paper, stream: Stream) -> int:
    text = f"{paper.title} {paper.abstract}".lower()
    title = paper.title.lower()

    if stream.require and not any(r.lower() in text for r in stream.require):
        return -1  # fails a hard requirement

    s = 0
    for kw in stream.boost:
        if kw.lower() in text:
            s += 1
            if kw.lower() in title:
                s += 1

    # An author/topic-filtered stream is already on-target: floor its score at 1
    # so relevant-but-keyword-light papers still surface.
    if stream.filter and s == 0:
        s = 1
    return s
