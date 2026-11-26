# Research Radar

Watches [OpenAlex](https://openalex.org) for **new academic papers** across a
set of [topics](#topics) (cognitive warfare, the semantic web, disinformation,
conceptual / model-driven engineering, law, ethics, complexity science and
more) and for **new work by a watchlist of researchers** in those fields
(following an OpenAlex author id is the equivalent of a Google Scholar "new
articles" alert). It then drafts ready-to-post **LinkedIn** updates for the
best of them a couple of times a week, and builds a most-cited
**[reading list](#reading-list--most-cited-papers-impact-not-freshness)** for the field.

You stay in the loop: the tool **drafts**, you review and post.

## How it works

Each run is a short pipeline. GitHub Actions runs it on a schedule, but it's
the same code you can run locally with `python -m radar.main`.

```
GitHub Actions (cron: Mon/Wed/Fri 07:00 UTC) ── or ── you, locally
  │
  ▼
radar/main.py  — orchestrates one run:
  1. fetch     for each stream in config.py, ask OpenAlex for works
               published in the last LOOKBACK_DAYS (10) days      → openalex.py
  2. dedupe    drop any work id already in state/seen.json         → main.py
  3. score     rank each paper by metadata quality; drop junk       → relevance.py
               (venue, doc type, reference depth, topic-fit, OA;
                a paper caught by several streams is kept once)
  4. pick      choose up to DRAFTS_PER_KIND (3) from EACH kind — keywords,
               authors, topics — so a broad topic can't crowd out the others
  5. draft     turn each pick into a LinkedIn post template       → report.py
  6. render    write everything to state/latest_report.md         → report.py
               (the picks as drafts + the rest as a digest list)
  7. save      mark the reported ids as seen (skipped on --dry-run)→ main.py
  │
  ▼
GitHub Actions then:
  • opens a GitHub Issue whose body is latest_report.md
  • commits the updated state/seen.json back to the repo
```

You open the issue on your phone, paste the drafts you like into LinkedIn,
tweak the one-line `[add your take]`, and close the issue. Papers already
reported never come back, so each issue is only what's genuinely new.

> **Note:** the radar never *reads* a paper for you. It finds papers and drafts
> a short blurb from the abstract/metadata — you open and read the ones you want.

## How the search works

"Searching" is just a set of OpenAlex `/works` queries — **one per stream**, run
every time the radar fires. Each stream (in `radar/config.py`) is one of three
matcher types:

| Matcher | OpenAlex filter it builds | Means |
|---|---|---|
| **Author** (watched researchers) | `author.id:A1\|A2\|…` | new work by any of these people |
| **Topic** | `topics.id:T10215` | anything OpenAlex classifies under this topic |
| **Search phrase** | `title_and_abstract.search:cognitive warfare` | these words appear in the title or abstract |

For each stream, `radar/openalex.py` sends **one** request to
`https://api.openalex.org/works` combining:

- `from_publication_date:<today − LOOKBACK_DAYS>` — only the last 10 days (the
  "new papers only" part);
- the stream's matcher (one row above);
- `sort=publication_date:desc` — newest first;
- `per-page=50` — cap per stream;
- `select=…` — only the fields used (title, authors, abstract, DOI, venue, type,
  open-access status, primary topic, reference count);
- an `Authorization: Bearer <OPENALEX_API_KEY>` header, so it draws on your own
  budget.

A concrete example — the "Semantic Web" topic stream becomes:

```
GET https://api.openalex.org/works
      ?filter=from_publication_date:2026-11-14,topics.id:T10215
      &sort=publication_date:desc
      &per-page=50
      &select=id,title,publication_date,type,primary_topic,open_access,authorships,...
```

So one run = **27 of these queries** ("last 10 days matching this stream, newest
first") — 10 keyword searches, 1 combined researcher query, and 16 topics (12
direct + 4 gated). OpenAlex does the finding; everything after — dedupe, scoring,
ranking — happens locally in Python (`main.py`).

## How papers are ranked

A paper that's only days old has **no citations yet**, so the radar can't rank
by impact. Instead it scores each paper on **metadata-quality proxies** that
exist at birth — signals of how *serious and credible* a paper is (not a
judgement of its ideas, which only reading it can give). Deliberately **not**
based on who wrote it or which stream matched: your streams decide what *enters*
the radar; the score decides what's worth reading within it.

| Signal | Points | Why |
|---|---:|---|
| Venue | up to 40 | peer-reviewed journal (DOAJ) > journal / conference > book > preprint |
| Document type | up to 20 | review/survey > research article > chapter > preprint |
| Reference depth | up to 15 | a 40+-reference paper is more substantial than a 3-reference note |
| Abstract present | +5 | a paper with an abstract is a more complete record than a bare stub |
| Topic-fit | up to 10 | how confidently OpenAlex classifies it (a clear subject, not a vague one) |
| Open access | +5 | tie-breaker — you can actually read it today |

Junk document types (editorials, errata, retractions, …) are dropped outright.

**Multi-criteria bonus.** A paper that trips more than one of your criteria — a
watched author *and* a watched topic, or two watched topics — is more clearly
on-target, so it gets `+MULTI_MATCH_BONUS` (default 8) per extra distinct
criterion, capped at `MULTI_MATCH_MAX` (24). Set the bonus to 0 to rank on
quality alone.

**Explainability.** Every draft and digest row shows both:

- **Captured because** — *why it entered the radar*: the exact criterion/criteria
  that matched (a named watched author, a watched topic + its id, or a search
  phrase). Papers hitting several list every reason.
- **Why picked** — *how it scored*: the plain-language quality breakdown above
  (plus the multi-criteria bonus when it applies).

Raising `MIN_SCORE` keeps only higher-quality papers; lowering it catches more.

The digest is a table of everything new that wasn't drafted, with
**date · access (🔓/🔒) · score · title · authors · captured because · topic ·
DOI · why**.

## What it watches

Everything is defined in `radar/config.py`. Three kinds of stream feed the radar:

- **Keyword searches** — a precise title/abstract phrase that catches *anyone*
  who uses it, not just your people or topics: *conceptual modelling*, *cognitive
  warfare*, *disinformation*, *information warfare*, *influence operations*,
  *information manipulation / FIMI*, *reflexive control*, *hybrid warfare*, and
  *OntoUML*. Add a phrase to the keyword block in `config.py` to watch more.
- **Watched researchers** — one flat list of OpenAlex **author ids**, all OR'd
  into a single query; following one is the equivalent of a Google Scholar "new
  articles" alert.
- **Topic streams** — one OpenAlex **topic id** each — *direct*, or *gated* by
  your terms when the topic is broad (see [Topics](#topics)).

Drafts are chosen **per kind** — up to `DRAFTS_PER_KIND` (3) from keywords,
authors, and topics each — so a broad topic can't crowd out your people or your
key terms.

### Watched researchers

One flat list (`PEOPLE` in `config.py`) — no sub-categories, just people whose
new work you always want to see. The whole list is a single OpenAlex query (ids
OR'd together). Edit the dict to follow or drop someone.

- **Giancarlo Guizzardi** `A5065297243` — Twente; UFO and OntoUML.
- **Tiago Prince Sales** `A5030998387` — Twente; OntoUML.
- **João Paulo A. Almeida** `A5063817933` — UFES, Brazil; gUFO.
- **Nicola Guarino** `A5053715134` — ISTC-CNR; OntoClean and DOLCE, the roots of UFO.
- **Barry Smith** `A5051216244` — Buffalo; BFO, the defence ontologies.
- **Valentina Presutti** `A5007281490` and **Aldo Gangemi** `A5065705742` —
  Bologna; ontology design patterns.
- **Maria Keet** `A5057850155` — Cape Town; her ontology-engineering textbook is free.
- **Pascal Hitzler** `A5006872667` — Kansas State; modular ontology modelling.
- **Aidan Hogan** `A5070504151` — University of Chile; the *Knowledge Graphs* book.
- **Paul Groth** `A5034924491` — Amsterdam; provenance and PROV-O.
- **Frank van Harmelen** `A5029130731` — VU Amsterdam; knowledge graphs combined with AI.
- **Ruben Verborgh** `A5055871472` and **Pieter Colpaert** `A5068448434` —
  Ghent; Linked Data.
- **Juan Sequeda** `A5014287041` — data.world; knowledge graphs and semantic data.
- **Frank Nack** `A5075446663` — Amsterdam; interactive multimedia, semantic media.
- **Panos Constantinides** `A5050801999` — digital innovation, information systems.
- **Lucas Introna** `A5079338334` — Lancaster; ethics & phenomenology of
  information systems.
- **Paul A. L. Ducheine** `A5060916131` — Amsterdam / NL Defence Academy;
  military law and cyber operations.
- **Bernard Claverie** `A5027932705` — Bordeaux INP; co-shaped the NATO
  cognitive-warfare concept.
- **Baptiste Prébot** `A5075868467` — CWDB maintainer; built the Cognitive
  Warfare Index, the first bibliographic database on the subject.
- **Maxime Audinet** `A5138999954` / `A5071977967` — IRSEM, Paris; Russian
  influence and the state media RT and Sputnik. (Two OpenAlex profiles, both followed.)
- **Stefan Soesanto** `A5048734240` — ETH Zurich; cyber conflict and
  information operations.
- **Han Bouwmeester** `A5078972793` — Netherlands Defence Academy; maskirovka,
  reflexive control, active measures (Utrecht PhD *Krym Nash*). Dutch — a strong
  potential contact.
- **Dima Adamsky** `A5005470460` — Reichman University, Israel; Russian
  strategic culture and cross-domain coercion.
- **Ofer Fridman** `A5037734689` — King's College London; Russian "hybrid
  warfare" as Russians themselves understand it.
- **Bettina Renz** `A5051215193` — Nottingham; Russian military power, and a
  critic of the hype around it.
- **Jānis Bērziņš** `A5092769843` — Latvian National Defence Academy; "new
  generation warfare". (Sparsely indexed in OpenAlex.)
- **Thomas Rid** `A5047539711` — Johns Hopkins SAIS; the history of active measures.
- **Samuel Woolley** `A5028631384` — University of Pittsburgh; computational propaganda.
- **Kate Starbird** `A5045494255` — University of Washington; participatory
  disinformation.
- **Yevgeniy Golovchenko** `A5085545989` — Copenhagen; computational studies of
  Russian disinformation.
- **Martin Innes** `A5026819080` — Cardiff; Russian information operations in Europe.
- **Sander van der Linden** `A5073961643` — Cambridge; inoculation against
  misinformation.
- **Stephan Lewandowsky** `A5017914184` — Bristol / Potsdam; the cognitive and
  psychological side of misinformation.
- **Vítor V. Vasconcelos** `A5036034260` — University of Amsterdam; collective
  behaviour and complex systems.
- **Mike Lees** `A5021090586` — University of Amsterdam; complex-systems simulation.

> To find anyone else's id, open their OpenAlex profile (or search
> `api.openalex.org/authors?search=Their Name`) and copy the `A…` id.

### Topics

Each OpenAlex topic is its own stream (the `TOPICS` / `GATED_TOPICS` dicts in
`config.py`); delete a line to stop watching it. Topics come in two kinds.

**Direct** — narrow and on-theme, so the topic tag alone is enough:

| Topic | OpenAlex id |
|---|---|
| Semantic Web and Ontologies | `T10215` |
| Model-Driven Software Engineering Techniques | `T11450` |
| Business Process Modeling and Analysis | `T10703` |
| Cybersecurity and Cyber Warfare Studies | `T12221` |
| European and Russian Geopolitical Military Strategies | `T13369` |
| Misinformation and Its Impacts | `T11147` |
| Military and Defense Studies | `T14086` |
| Military Strategy and Technology | `T12888` |
| War, Ethics, and Justification | `T12957` |
| Freedom of Expression and Defamation | `T14432` |
| Ethics and Social Impacts of AI | `T10883` |
| Logic, Reasoning, and Knowledge | `T11010` |

**Gated** (`GATED_TOPICS`) — relevant but broad, so a paper is kept only if its
title/abstract also mentions one of your `GATE_TERMS` (disinformation, influence
operations, cognitive / information / hybrid warfare, reflexive control, cyber,
Russia, ontology, knowledge graph, conceptual model, …):

| Topic | OpenAlex id |
|---|---|
| International Law and Human Rights | `T10749` |
| Terrorism, Counterterrorism, and Political Violence | `T10994` |
| Information Systems Theories and Implementation | `T11024` |
| Philosophy, Ethics, and Existentialism † | `T12366` |

> † You listed this as *"Phenomenology, Ethics, and Existentialism"*; the actual
> OpenAlex topic is *"Philosophy, Ethics, and Existentialism"* (`T12366`).
>
> **Dropped as too broad / off-theme** — they scored high on quality but weren't
> about your interests: general software-engineering methods, Management &
> Organizational Studies, Graph Theory, Database Systems, Graph Neural Networks,
> Web Applications, Scientific Computing, Topic Modelling, Research Data
> Management, Human-Automation Interaction, Posthumanist Ethics. Knowledge graphs
> have no clean OpenAlex topic of their own — they're covered by *Semantic Web
> and Ontologies*.

## Complexity science — background & self-study

The radar can follow *researchers* but not books or courses. For the
foundations of complexity and systems thinking, work through this material
directly:

- **Donella Meadows, *Thinking in Systems*** — short, the best starting point.
- **Melanie Mitchell, *Complexity: A Guided Tour*.**
- **[NetLogo](https://ccl.northwestern.edu/netlogo/) model library** — start
  with the virus and rumour-spread models.
- **[Santa Fe Institute — Complexity Explorer](https://www.complexityexplorer.org/)**
  — free online courses.

Vasconcelos and Lees (tracked in the watchlist above) cover the current
research side.

## Project structure

```
research-radar/
├── radar/                  the Python package (one job per file)
│   ├── config.py           WHAT to watch: keyword searches, the PEOPLE
│   │                       watchlist, TOPICS / GATED_TOPICS, and the tuning knobs
│   ├── openalex.py         FETCH: thin OpenAlex /works client; builds each
│   │                       query and normalises results into a Paper
│   ├── relevance.py        SCORE: metadata-quality scoring + the require filter
│   ├── report.py           RENDER: Paper → Markdown — LinkedIn drafts, the
│   │                       digest, and the --canon most-cited reading list
│   └── main.py             RUN: the pipeline + CLI, plus the seen.json dedupe
│                           store and the --download open-access PDF fetch
│
├── state/                  run output + memory
│   ├── seen.json           work ids already reported (committed dedupe ledger)
│   ├── latest_report.md    the most recent run's drafts + digest (gitignored)
│   └── reading_list.md     the --canon output (gitignored)
│
├── .github/workflows/
│   ├── watch.yml           the scheduled unattended run (fetch → issue → commit)
│   └── reading-list.yml    the monthly --canon run (build → issue)
│
├── requirements.txt        just `requests`
└── README.md
```

The data object that flows through the whole pipeline is `Paper`
(defined in `openalex.py`): fetched by `openalex`, scored by `relevance`,
rendered to Markdown by `report`, and orchestrated by `main`.

## Run it locally

```bash
pip install -r requirements.txt
python -m radar.main --dry-run    # safe: doesn't update seen-state
python -m radar.main              # real run: writes state/latest_report.md
python -m radar.main --download   # also save open-access PDFs to papers/
python -m radar.main --canon      # build the most-cited reading list
```

Open `state/latest_report.md` to see the drafts.

### Reading list — most-cited papers (impact, not freshness)

The main flow answers *"what's new?"*. `--canon` answers a different question —
*"what does the field actually lean on?"* — and writes a separate
`state/reading_list.md`. Because these papers already have citations, they're
ranked by **citations directly** (no birth-time proxies). For each topic in
`CANON_TOPIC_IDS` it builds two lists:

- **🏛️ All-time canon** — most cited ever: the foundational reading.
- **📈 Rising** — the last `RISING_SINCE_YEARS` (default 3), ranked by
  **citations-per-year**, so a fast-climbing recent paper isn't buried under an
  older one.

It's a reference doc: not drafted, not deduped, regenerate it whenever. Keep
`CANON_TOPIC_IDS` to a few core topics (ids must exist in `TOPICS`); defaults to
cyber/cognitive-warfare, misinformation, and the conceptual-modelling topics.

GitHub Actions also builds it **monthly** (`.github/workflows/reading-list.yml`,
1st of the month) and opens an issue with the list — so you get the impact view
without running anything locally.

### Downloading papers to read

`--download` saves a **local reading pile**: every **open-access** paper scoring
at least `DOWNLOAD_MIN_SCORE` (default 70) is downloaded to the gitignored
`papers/` folder — named `DATE__scoreNN__Title__id.pdf` — up to `DOWNLOAD_MAX`
per run. Closed-access papers are never downloaded (they still appear in the
digest, marked 🔒). When a link is a landing page rather than a direct PDF, a
small `.link.txt` is saved instead. Each downloaded paper shows a
**📥 saved** link in the report.

**Preprints** (unreviewed manuscripts on arXiv/SSRN/etc.) usually score below 70,
so they aren't saved by default. In a few chosen areas, though, the early work is
worth having: a preprint there is downloaded even below the bar (down to
`DOWNLOAD_PREPRINT_MIN_SCORE`). Those areas are **disinformation, conceptual
models, and cognitive warfare** — a preprint qualifies when its own primary topic
is in `PREPRINT_TOPICS`, or it was caught by one of your keyword searches
(`PREPRINT_STREAMS` is derived from them). Peer-reviewed work everywhere else
still needs `DOWNLOAD_MIN_SCORE`.

This is a **local-only** feature: the unattended GitHub Actions run can't keep
files (its machine is wiped each run), so it never downloads — it just opens the
issue with the digest as usual.

## Deploy (GitHub Actions — unattended)

1. Create a GitHub repo and push this project to it.
2. The workflow in `.github/workflows/watch.yml` runs automatically on the cron
   schedule, and you can trigger it any time from the **Actions** tab
   ("Run workflow"). It uses the built-in `GITHUB_TOKEN` — no setup needed.
3. **Optional:** add a repo *variable* `OPENALEX_MAILTO` (an address you choose)
   to join OpenAlex's faster "polite pool". Not needed once you have a key below.
4. **Recommended — your own OpenAlex budget:** add a repo *secret*
   `OPENALEX_API_KEY`. Without a key, requests share a small free budget tied to
   your network's IP address (and can hit "Rate limit exceeded" if that pool is
   spent); a personal key is free and has its own **$1/day** budget. Get one at
   <https://help.openalex.org/api/authentication/> (or an agent can POST your
   email to `https://api.openalex.org/api-keys`), then click the activation link
   emailed to you. The key is sent as an `Authorization: Bearer` header — keep it
   out of committed files.

## Tuning

- `LOOKBACK_DAYS` — how far back each run looks (keep a margin over the cadence).
- `DRAFTS_PER_KIND` — full drafts per *kind* (keywords / authors / topics) per
  run — so at most 3× this many drafts (the rest become a digest list). Lower it
  to 2 if that's too many to scan.
- `PER_TOPIC_CAP` — within the topic kind, cap drafts from any single topic so
  the topic picks spread across different topics.
- `MIN_SCORE` — the quality floor (see [How papers are ranked](#how-papers-are-ranked)).
  Raise it to keep only serious venues; lower it to catch preprints and more.
- `MULTI_MATCH_BONUS` / `MULTI_MATCH_MAX` — reward for a paper hitting several of
  your criteria at once (set the bonus to 0 to rank on quality alone).
- `DOWNLOAD_MIN_SCORE` / `DOWNLOAD_MAX` — quality bar and per-run cap for the
  open-access PDFs saved by `--download` (see
  [Downloading papers](#downloading-papers-to-read)).
- `PREPRINT_TOPICS` / `PREPRINT_STREAMS` / `DOWNLOAD_PREPRINT_MIN_SCORE` — areas
  where preprints are also saved (below the normal bar), and the floor for them.
  Add a topic id or stream key to widen which areas keep early work.
- `CANON_TOPIC_IDS` / `CANON_PER_TOPIC` / `RISING_PER_TOPIC` / `RISING_SINCE_YEARS`
  — which topics the `--canon` reading list covers and how many papers each list
  shows (see [Reading list](#reading-list--most-cited-papers-impact-not-freshness)).
- `TOPICS` / `GATED_TOPICS` / `GATE_TERMS` — what topics you watch, and (for the
  broad `GATED_TOPICS`) the terms that must appear for a paper to count. Move a
  topic between the two dicts to tighten or loosen it; prune `TOPICS` to cut noise.
- `require` — optional per-stream noise filter (a phrase that must appear); this
  is the same mechanism `GATE_TERMS` uses, and you can set it on any stream.
- Cron schedule — edit the `cron:` line in `.github/workflows/watch.yml`.
  It currently runs **Mon/Wed/Fri at 07:00 UTC** (`0 7 * * 1,3,5`); change the
  day field (`1,3,5`) to pick other days — e.g. `2,5` for Tue/Fri.
