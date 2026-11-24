# Research Radar

Watches [OpenAlex](https://openalex.org) for **new academic papers** across a
set of [topics](#topics) (cognitive warfare, the semantic web, disinformation,
conceptual / model-driven engineering, law, ethics, complexity science and
more) and for **new work by a watchlist of researchers** in those fields
(following an OpenAlex author id is the equivalent of a Google Scholar "new
articles" alert). It then drafts ready-to-post **LinkedIn** updates for the
best of them a couple of times a week.

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
  2. dedupe    drop any work id already in state/seen.json         → store.py
  3. score     rank each paper by metadata quality; drop junk       → relevance.py
               (venue, doc type, reference depth, topic-fit, OA;
                a paper caught by several streams is kept once)
  4. pick      choose up to MAX_DRAFTS (3), spread across streams
               so one busy topic can't crowd out the others
  5. draft     turn each pick into a LinkedIn post                 → drafter.py
               (plain template, or Claude-polished if a key is set)
  6. render    write everything to state/latest_report.md         → deliver.py
               (the picks as drafts + the rest as a digest list)
  7. save      mark the reported ids as seen (skipped on --dry-run)→ store.py
  │
  ▼
GitHub Actions then:
  • opens a GitHub Issue whose body is latest_report.md
  • commits the updated state/seen.json back to the repo
```

You open the issue on your phone, paste the drafts you like into LinkedIn,
tweak the one-line `[add your take]`, and close the issue. Papers already
reported never come back, so each issue is only what's genuinely new.

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
| Topic-fit | up to 10 | how confidently OpenAlex classifies it (a clear subject, not a vague one) |
| Open access | +5 | tie-breaker — you can actually read it today |

Junk document types (editorials, errata, retractions, …) are dropped outright.
Every draft and digest row shows its **score and a plain-language "why"**, so you
can see the reasoning and retune it. Raising `MIN_SCORE` keeps only
higher-quality papers; lowering it catches more.

The digest is a table of everything new that wasn't drafted, with
**date · access (🔓/🔒) · score · title · authors · topic · DOI · why**.

## What it watches

Everything is defined in `radar/config.py`. Three kinds of stream feed the radar:

- **Search streams** — a title/abstract phrase. Two: *conceptual modelling* and
  *cognitive warfare*.
- **Researcher watchlists** — OpenAlex **author ids**; following one is the
  equivalent of a Google Scholar "new articles" alert. Grouped one query per area.
- **Topic streams** — one OpenAlex **topic id** each (see [Topics](#topics)).

### My favourite researchers

A hand-picked list I always want to see (`FAVOURITE_PEOPLE` in `config.py`):

- **Giancarlo Guizzardi** `A5065297243` — Twente; UFO and OntoUML.
- **Paul A. L. Ducheine** `A5060916131` — Amsterdam / NL Defence Academy;
  military law and cyber operations.
- **Paul Groth** `A5034924491` — Amsterdam; provenance and PROV-O.
- **Juan Sequeda** `A5014287041` — knowledge graphs and semantic data (data.world).
- **Lucas Introna** `A5079338334` — Lancaster; ethics & phenomenology of
  information systems.
- **Frank Nack** `A5075446663` — Amsterdam; interactive multimedia, semantic media.
- **Panos Constantinides** `A5050801999` — digital innovation, information systems.

### Researcher watchlists

Grouped by area; each group is one OpenAlex query (ids OR'd together). Edit the
dicts at the top of `radar/config.py` to follow or drop someone.

**Cognitive warfare (the NATO concept / CWDB core)**

- **Bernard Claverie** `A5027932705` — Emeritus Professor of Cognitive Sciences
  at Bordeaux Institute of Technology; co-shaped the NATO concept.
- **Baptiste Prébot** `A5075868467` — Claverie's co-author and a CWDB
  maintainer; built the Cognitive Warfare Index, the first bibliographic
  database on the subject.
- **Maxime Audinet** `A5138999954` / `A5071977967` — IRSEM, Paris; Russian
  influence and the state media RT and Sputnik; works with the Bordeaux group.
  (Two OpenAlex profiles, both followed.)

**Russian strategic thinking and deception**

- **Han Bouwmeester** `A5078972793` — Associate Professor of military strategy
  and land operations, Netherlands Defence Academy; Utrecht PhD *Krym Nash* on
  maskirovka, reflexive control, active measures, agents of influence,
  spetspropaganda, agitprop. Dutch — a strong potential contact.
- **Dima Adamsky** `A5005470460` — Reichman University, Israel; Russian
  strategic culture and cross-domain coercion.
- **Ofer Fridman** `A5037734689` — King's College London; Russian "hybrid
  warfare" as Russians themselves understand it.
- **Bettina Renz** `A5051215193` — Nottingham; Russian military power, and a
  critic of the hype around it.
- **Jānis Bērziņš** `A5092769843` — Latvian National Defence Academy; "new
  generation warfare". (Sparsely indexed in OpenAlex.)

**Disinformation and computational propaganda**

- **Thomas Rid** `A5047539711` — Johns Hopkins SAIS; the history of active measures.
- **Samuel Woolley** `A5028631384` — University of Pittsburgh; William S.
  Dietrich II Endowed Chair in Disinformation Studies; computational propaganda.
- **Kate Starbird** `A5045494255` — University of Washington; participatory
  disinformation.
- **Yevgeniy Golovchenko** `A5085545989` — Copenhagen; computational studies of
  Russian disinformation.
- **Martin Innes** `A5026819080` — Cardiff; Russian information operations in Europe.
- **Sander van der Linden** `A5073961643` — Cambridge; inoculation against
  misinformation.
- **Stephan Lewandowsky** `A5017914184` — Bristol; the cognitive and
  psychological side of misinformation.

**Ontology and semantic modelling**

- **Giancarlo Guizzardi** `A5065297243` — Twente; UFO and OntoUML.
  (Also in *My favourite researchers*.)
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
  Ghent; Linked Data. (Relevant if you go for a Ghent PhD.)

**Complexity science**

- **Vítor V. Vasconcelos** `A5036034260` — University of Amsterdam; collective
  behaviour and complex systems.
- **Mike Lees** `A5021090586` — University of Amsterdam; complex-systems simulation.

> To find anyone else's id, open their OpenAlex profile (or search
> `api.openalex.org/authors?search=Their Name`) and copy the `A…` id.

### Topics

Each OpenAlex topic is its own stream (the `TOPICS` dict in `config.py`); delete
a line to stop watching it. **⚠ = broad, high-volume** topic — expect a long
digest (tune with `MIN_SCORE` or drop it).

| Topic | OpenAlex id |
|---|---|
| Semantic Web and Ontologies | `T10215` |
| Model-Driven Software Engineering Techniques | `T11450` |
| Cybersecurity and Cyber Warfare Studies | `T12221` |
| International Law and Human Rights ⚠ | `T10749` |
| European and Russian Geopolitical Military Strategies | `T13369` |
| Human-Automation Interaction and Safety ⚠ | `T10525` |
| Military and Defense Studies | `T14086` |
| Terrorism, Counterterrorism, and Political Violence ⚠ | `T10994` |
| Misinformation and Its Impacts | `T11147` |
| Freedom of Expression and Defamation | `T14432` |
| Posthumanist Ethics and Activism | `T10738` |
| Management and Organizational Studies | `T10344` |
| Graph Theory and Algorithms | `T12292` |
| Advanced Database Systems and Queries ⚠ | `T10317` |
| Advanced Graph Neural Networks | `T11273` |
| Web Applications and Data Management | `T12601` |
| Scientific Computing and Data Management | `T11986` |
| Complexity and Algorithms in Graphs ⚠ | `T10720` |
| Topic Modeling | `T10028` |
| Logic, Reasoning, and Knowledge | `T11010` |
| Ethics and Social Impacts of AI | `T10883` |
| Research Data Management Practices | `T11937` |
| Information Systems Theories and Implementation | `T11024` |
| Philosophy, Ethics, and Existentialism † | `T12366` |
| Posttraumatic Stress Disorder Research ↓ | `T10242` |
| War, Ethics, and Justification | `T12957` |
| Military Strategy and Technology | `T12888` |

> † You listed this as *"Phenomenology, Ethics, and Existentialism"*; the actual
> OpenAlex topic is *"Philosophy, Ethics, and Existentialism"* (`T12366`).
>
> ↓ **Low priority** (`LOW_PRIORITY_TOPICS` in `config.py`): still watched and
> shown in the digest, but score-penalised so it doesn't take draft slots.
>
> *"Shaping Societal Transitions"* was **dropped** — no matching OpenAlex topic.

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
│   ├── config.py           WHAT to watch: favourites, author watchlists, the
│   │                       TOPICS dict, and knobs (LOOKBACK_DAYS, MIN_SCORE…)
│   ├── openalex.py         HOW to fetch: thin OpenAlex /works client;
│   │                       builds each query and normalises results into Paper
│   ├── relevance.py        HOW to score: keyword scoring + the require filter;
│   │                       floors author/topic streams so on-target papers pass
│   ├── drafter.py          HOW to write: Paper → LinkedIn post (template, or
│   │                       Claude-polished when ANTHROPIC_API_KEY is set)
│   ├── deliver.py          HOW to present: render drafts + digest to Markdown
│   │                       and write state/latest_report.md
│   ├── store.py            MEMORY: the seen.json dedupe store (is_new / mark)
│   └── main.py             the pipeline that ties the six together
│
├── state/                  run output + memory (committed so it persists)
│   ├── seen.json           work ids already reported (the dedupe ledger)
│   └── latest_report.md    the most recent run's drafts + digest
│
├── .github/workflows/
│   └── watch.yml           the scheduled unattended run (fetch → issue → commit)
│
├── requirements.txt        requests (needed) + anthropic (optional, for drafts)
└── README.md
```

The data object that flows through the whole pipeline is `Paper`
(defined in `openalex.py`): fetched by `openalex`, scored by `relevance`,
turned into text by `drafter`, and listed by `deliver`.

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
5. **Recommended — your own OpenAlex budget:** add a repo *secret*
   `OPENALEX_API_KEY`. Without a key, requests share a small free budget tied to
   your network's IP address (and can hit "Rate limit exceeded" if that pool is
   spent); a personal key is free and has its own **$1/day** budget. Get one at
   <https://help.openalex.org/api/authentication/> (or an agent can POST your
   email to `https://api.openalex.org/api-keys`), then click the activation link
   emailed to you. The key is sent as an `Authorization: Bearer` header — keep it
   out of committed files.

## Tuning

- `LOOKBACK_DAYS` — how far back each run looks (keep a margin over the cadence).
- `MAX_DRAFTS` — full drafts per run (the rest become a digest list).
- `MIN_SCORE` — the quality floor (see [How papers are ranked](#how-papers-are-ranked)).
  Raise it to keep only serious venues; lower it to catch preprints and more.
- `LOW_PRIORITY_TOPICS` — topic ids to keep watching but keep *out* of drafts
  (penalised, still shown in the digest).
- `boost` / `require` keyword lists per stream in `config.py`.
- Cron schedule — edit the `cron:` line in `.github/workflows/watch.yml`.
  It currently runs **Mon/Wed/Fri at 07:00 UTC** (`0 7 * * 1,3,5`); change the
  day field (`1,3,5`) to pick other days — e.g. `2,5` for Tue/Fri.
