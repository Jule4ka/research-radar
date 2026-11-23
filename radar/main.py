"""Orchestrate one Research Radar run.

  fetch each stream -> drop seen ids -> score -> rank -> draft top N
  -> render report -> mark seen -> save state.

Flags:
  --dry-run   do everything except marking papers as seen (safe to re-run)
"""

from __future__ import annotations

import argparse

from . import config, deliver, drafter, relevance
from .openalex import Paper, fetch_stream
from .store import SeenStore


def run(dry_run: bool = False) -> str:
    store = SeenStore()
    scored: list[Paper] = []

    by_key = {s.key: s for s in config.STREAMS}
    for stream in config.STREAMS:
        try:
            papers = fetch_stream(stream, config.LOOKBACK_DAYS, config.PER_PAGE)
        except Exception as e:  # one stream failing shouldn't sink the run
            print(f"[warn] stream {stream.key} failed: {e}")
            continue
        for p in papers:
            if not store.is_new(p.short_id):
                continue
            p.score = relevance.score(p, stream)
            if p.score >= config.MIN_SCORE:
                scored.append(p)

    # Highest score first, then newest.
    scored.sort(key=lambda p: (p.score, p.date), reverse=True)

    # Diversify drafts across streams: take the best unused paper from each
    # stream in turn until MAX_DRAFTS is reached, so one busy topic (e.g.
    # semantic web) can't crowd out the others.
    top: list[Paper] = []
    picked: set[str] = set()
    while len(top) < config.MAX_DRAFTS:
        progressed = False
        for key in by_key:
            if len(top) >= config.MAX_DRAFTS:
                break
            for p in scored:
                if p.stream == key and p.short_id not in picked:
                    top.append(p)
                    picked.add(p.short_id)
                    progressed = True
                    break
        if not progressed:
            break

    rest = [p for p in scored if p.short_id not in picked]

    drafts = [(p, drafter.make_draft(p)) for p in top]
    markdown = deliver.render(drafts, rest)
    deliver.write_file(markdown)

    if not dry_run:
        for p in scored:
            store.mark(p.short_id)
        store.save()

    print(f"[radar] {len(scored)} new papers; {len(top)} drafted; "
          f"{'DRY RUN (state unchanged)' if dry_run else 'state saved'}")
    return markdown


def main() -> None:
    ap = argparse.ArgumentParser(description="Research Radar")
    ap.add_argument("--dry-run", action="store_true",
                    help="don't mark papers as seen (safe to re-run)")
    args = ap.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
