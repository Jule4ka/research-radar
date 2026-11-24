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


# --- Author watchlists -------------------------------------------------------
# Following a researcher by OpenAlex author id is the equivalent of a Google
# Scholar "new articles" alert. Each group below becomes ONE OpenAlex query:
# the ids are OR'd together with "|". To follow/drop someone, edit the dict.
# (id -> name is for your reference; only the id is sent to OpenAlex.)

COGWAR_PEOPLE = {
    "A5027932705": "Bernard Claverie (Bordeaux INP) — NATO cognitive warfare concept",
    "A5075868467": "Baptiste Prébot — Cognitive Warfare Index, CWDB",
    "A5138999954": "Maxime Audinet (IRSEM) — Russian influence, RT/Sputnik",
    "A5071977967": "Maxime Audinet (IRSEM) — second OpenAlex profile",
}

RUSSIA_PEOPLE = {
    "A5078972793": "Han Bouwmeester (NL Defence Academy) — maskirovka, reflexive control",
    "A5005470460": "Dima/Dmitry Adamsky (Reichman) — Russian strategic culture",
    "A5037734689": "Ofer Fridman (KCL) — Russian 'hybrid warfare'",
    "A5051215193": "Bettina Renz (Nottingham) — Russian military power",
    "A5092769843": "Jānis Bērziņš (Latvian NDA) — new generation warfare",
}

DISINFO_PEOPLE = {
    "A5047539711": "Thomas Rid (Johns Hopkins SAIS) — active measures",
    "A5028631384": "Samuel Woolley (Pittsburgh) — computational propaganda",
    "A5045494255": "Kate Starbird (UW) — participatory disinformation",
    "A5085545989": "Yevgeniy Golovchenko (Copenhagen) — Russian disinformation",
    "A5026819080": "Martin Innes (Cardiff) — information operations in Europe",
    "A5073961643": "Sander van der Linden (Cambridge) — inoculation",
    "A5017914184": "Stephan Lewandowsky (Bristol/Potsdam) — misinformation psychology",
}

ONTO_PEOPLE = {
    # Guizzardi has his own dedicated stream below.
    "A5030998387": "Tiago Prince Sales (Twente) — OntoUML",
    "A5063817933": "João Paulo A. Almeida (UFES) — gUFO",
    "A5053715134": "Nicola Guarino (ISTC-CNR) — DOLCE, OntoClean",
    "A5051216244": "Barry Smith (Buffalo) — BFO, defence ontologies",
    "A5007281490": "Valentina Presutti (Bologna) — ontology design patterns",
    "A5065705742": "Aldo Gangemi (Bologna) — ontology design patterns",
    "A5057850155": "Maria Keet (Cape Town) — ontology engineering",
    "A5006872667": "Pascal Hitzler (Kansas State) — modular ontology modelling",
    "A5070504151": "Aidan Hogan (Chile) — knowledge graphs",
    "A5034924491": "Paul Groth (Amsterdam) — provenance, PROV-O",
    "A5029130731": "Frank van Harmelen (VU Amsterdam) — knowledge graphs + AI",
    "A5055871472": "Ruben Verborgh (Ghent) — linked data",
    "A5068448434": "Pieter Colpaert (Ghent) — linked data",
}

COMPLEXITY_PEOPLE = {
    "A5036034260": "Vítor V. Vasconcelos (UvA) — collective behaviour, complexity",
    "A5021090586": "Michael (Mike) Lees (UvA) — complex-systems simulation",
}

# My favourite researchers — a hand-picked list I always want to see.
# (Guizzardi and Groth also appear in the area watchlists above; OpenAlex and
# the pipeline de-duplicate, so listing them here too is harmless.)
FAVOURITE_PEOPLE = {
    "A5065297243": "Giancarlo Guizzardi (Twente) — UFO, OntoUML",
    "A5060916131": "Paul A. L. Ducheine (Amsterdam/NLDA) — military law, cyber operations",
    "A5034924491": "Paul Groth (Amsterdam) — provenance, PROV-O",
    "A5014287041": "Juan Sequeda (data.world) — knowledge graphs, semantic data",
    "A5079338334": "Lucas Introna (Lancaster) — ethics & phenomenology of information systems",
    "A5075446663": "Frank Nack (Amsterdam) — interactive multimedia, semantic media",
    "A5050801999": "Panos Constantinides — digital innovation, information systems",
}


# --- Topics ------------------------------------------------------------------
# Each OpenAlex topic becomes its own stream (one /works query per topic), so
# you can see which topic matched and prune a noisy one by deleting its line.
# Find a topic id at https://api.openalex.org/topics?search=Your+Topic+Name
TOPICS = {
    "T10215": "Semantic Web and Ontologies",
    "T11450": "Model-Driven Software Engineering Techniques",
    "T12221": "Cybersecurity and Cyber Warfare Studies",
    "T10749": "International Law and Human Rights",
    "T13369": "European and Russian Geopolitical Military Strategies",
    "T10525": "Human-Automation Interaction and Safety",
    "T14086": "Military and Defense Studies",
    "T10994": "Terrorism, Counterterrorism, and Political Violence",
    "T11147": "Misinformation and Its Impacts",
    "T14432": "Freedom of Expression and Defamation",
    "T10738": "Posthumanist Ethics and Activism",
    "T10344": "Management and Organizational Studies",
    "T12292": "Graph Theory and Algorithms",
    "T10317": "Advanced Database Systems and Queries",
    "T11273": "Advanced Graph Neural Networks",
    "T12601": "Web Applications and Data Management",
    "T11986": "Scientific Computing and Data Management",
    "T10720": "Complexity and Algorithms in Graphs",
    "T10028": "Topic Modeling",
    "T11010": "Logic, Reasoning, and Knowledge",
    "T10883": "Ethics and Social Impacts of AI",
    "T11937": "Research Data Management Practices",
    "T11024": "Information Systems Theories and Implementation",
    "T10242": "Posttraumatic Stress Disorder Research",
    "T12957": "War, Ethics, and Justification",
    "T12888": "Military Strategy and Technology",
    # You wrote "Phenomenology, Ethics, and Existentialism"; the OpenAlex topic
    # is actually named "Philosophy, Ethics, and Existentialism".
    "T12366": "Philosophy, Ethics, and Existentialism",
    # ("Shaping Societal Transitions" dropped — no matching OpenAlex topic.)
}

# Topics you still want watched (they appear in the digest) but NOT featured as
# drafts — their score is penalised so higher-priority work wins the draft slots.
LOW_PRIORITY_TOPICS = {
    "T10242",  # Posttraumatic Stress Disorder Research — tangential, watch only
}


def _authors(people: dict[str, str]) -> str:
    """Build an OpenAlex author.id filter fragment that ORs everyone together."""
    return "author.id:" + "|".join(people)


STREAMS: list[Stream] = [
    # --- Search streams (title/abstract phrase) -----------------------------
    Stream(
        key="conceptual_modelling",
        label="Conceptual modelling (field)",
        search="conceptual modeling",
        boost=["ontology", "ontuml", "ontouml", "enterprise", "domain model",
               "data model", "er model", "metamodel", "modeling language"],
        require=["conceptual model", "conceptual modeling", "conceptual modelling"],
    ),
    Stream(
        key="cognitive_warfare",
        label="Cognitive warfare",
        search="cognitive warfare",
        boost=["cognitive security", "psychological", "influence", "military",
               "defence", "defense", "hybrid warfare", "information warfare"],
    ),

    # --- Researcher watchlists (one query per group; see dicts above) -------
    Stream(
        key="favourites",
        label="My favourite researchers (watchlist)",
        filter=_authors(FAVOURITE_PEOPLE),
    ),
    Stream(
        key="cogwar_people",
        label="Cognitive-warfare researchers (watchlist)",
        filter=_authors(COGWAR_PEOPLE),
    ),
    Stream(
        key="russia_people",
        label="Russian strategy & deception researchers (watchlist)",
        filter=_authors(RUSSIA_PEOPLE),
    ),
    Stream(
        key="disinfo_people",
        label="Disinformation researchers (watchlist)",
        filter=_authors(DISINFO_PEOPLE),
    ),
    Stream(
        key="onto_people",
        label="Ontology & semantic-modelling researchers (watchlist)",
        filter=_authors(ONTO_PEOPLE),
    ),
    Stream(
        key="complexity_people",
        label="Complexity-science researchers (watchlist)",
        filter=_authors(COMPLEXITY_PEOPLE),
    ),
]

# --- Topic streams (generated: one per entry in TOPICS) ---------------------
STREAMS += [
    Stream(key=f"topic_{tid}", label=name, filter=f"topics.id:{tid}")
    for tid, name in TOPICS.items()
]

# How many days back to look on each run (a safety margin over the cron cadence).
LOOKBACK_DAYS = 10

# Minimum relevance score (see relevance.py) for a paper to be eligible for a draft.
MIN_SCORE = 1

# How many full LinkedIn drafts to generate per run. The rest go in a digest list.
MAX_DRAFTS = 3

# Per-page cap when pulling from OpenAlex (newest first).
PER_PAGE = 50
