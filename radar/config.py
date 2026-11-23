"""Configuration for Research Radar.

Each STREAM becomes one OpenAlex /works query. A stream is matched by either:
  - an OpenAlex `filter` fragment (e.g. an author id or topic id), and/or
  - a `search` string applied to title + abstract (title_and_abstract.search).

Tune the keyword lists in `boost` / `require` to cut noise without missing papers.
"""

from dataclasses import dataclass, field


@dataclass
class Stream:
    key: str                      # short id, used in state + labels
    label: str                    # human-readable name shown in the digest
    filter: str = ""              # OpenAlex filter fragment, e.g. "author.id:A5065297243"
    search: str = ""              # title_and_abstract.search phrase
    boost: list[str] = field(default_factory=list)   # keywords that raise relevance
    require: list[str] = field(default_factory=list)  # if set, at least one must appear


STREAMS: list[Stream] = [
    Stream(
        key="guizzardi",
        label="Giancarlo Guizzardi (author)",
        filter="author.id:A5065297243",
        # Author stream is already precise; no keyword filtering needed.
    ),
    Stream(
        key="conceptual_modelling",
        label="Conceptual modelling (field)",
        search="conceptual modeling",
        boost=["ontology", "ontuml", "ontouml", "enterprise", "domain model",
               "data model", "er model", "metamodel", "modeling language"],
        require=["conceptual model", "conceptual modeling", "conceptual modelling"],
    ),
    Stream(
        key="semantic_web",
        label="Semantic web",
        filter="topics.id:T10215",
        boost=["knowledge graph", "sparql", "rdf", "owl", "linked data",
               "ontology", "reasoning", "schema"],
    ),
    Stream(
        key="disinformation",
        label="Disinformation",
        filter="topics.id:T11147",
        boost=["disinformation", "propaganda", "influence operation", "fake news",
               "bot", "coordinated", "narrative", "deepfake", "fact-check"],
    ),
    Stream(
        key="cognitive_warfare",
        label="Cognitive warfare",
        search="cognitive warfare",
        boost=["cognitive security", "psychological", "influence", "military",
               "defence", "defense", "hybrid warfare", "information warfare"],
    ),
]

# How many days back to look on each run (a safety margin over the cron cadence).
LOOKBACK_DAYS = 10

# Minimum relevance score (see relevance.py) for a paper to be eligible for a draft.
MIN_SCORE = 1

# How many full LinkedIn drafts to generate per run. The rest go in a digest list.
MAX_DRAFTS = 3

# Per-page cap when pulling from OpenAlex (newest first).
PER_PAGE = 50
