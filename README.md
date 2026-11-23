# Research Radar

Watches [OpenAlex](https://openalex.org) for **new academic papers** on
cognitive warfare, the semantic web, disinformation, and conceptual modelling
(including everything authored by Giancarlo Guizzardi), and drafts
ready-to-post **LinkedIn** updates for the best of them a couple of times a week.

You stay in the loop: the tool **drafts**, you review and post.

## How it works

```
cron (Tue + Fri)
  → query each stream on OpenAlex for papers in the last 10 days
  → drop papers already seen (state/seen.json)
  → score for relevance, drop noise
  → generate up to 3 LinkedIn drafts (spread across streams)
  → open a GitHub Issue with the drafts + a digest of the rest
  → commit updated seen-state back to the repo
```

You open the issue on your phone, paste the drafts you like into LinkedIn,
tweak the one-line `[add your take]`, and close the issue.

## The streams

Edit `radar/config.py` to tune them.

| Stream | How it's matched |
|---|---|
| Giancarlo Guizzardi | OpenAlex author `A5065297243` |
| Conceptual modelling | title/abstract search + keyword filter |
| Semantic web | OpenAlex topic `T10215` |
| Disinformation | OpenAlex topic `T11147` |
| Cognitive warfare | title/abstract search |

## Run it locally

```bash
pip install -r requirements.txt
python -m radar.main --dry-run   # safe: doesn't update seen-state
python -m radar.main             # real run: writes state/latest_report.md
```

Open `state/latest_report.md` to see the drafts.

## Deploy (GitHub Actions — unattended)

1. Create a GitHub repo and push this project to it.
2. The workflow in `.github/workflows/watch.yml` runs automatically on the cron
   schedule, and you can trigger it any time from the **Actions** tab
   ("Run workflow"). It uses the built-in `GITHUB_TOKEN` — no setup needed.
3. **Optional — nicer drafts:** add a repo secret `ANTHROPIC_API_KEY` to have
   Claude write the posts in a more natural voice. Without it, a clean template
   is used.
4. **Optional:** add a repo *variable* `OPENALEX_MAILTO` (an address you choose)
   to join OpenAlex's faster "polite pool".

## Tuning

- `LOOKBACK_DAYS` — how far back each run looks (keep a margin over the cadence).
- `MAX_DRAFTS` — full drafts per run (the rest become a digest list).
- `MIN_SCORE` — raise to be stricter; lower to catch more.
- `boost` / `require` keyword lists per stream in `config.py`.
- Cron schedule — edit the `cron:` line in the workflow.
