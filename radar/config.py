"""Configuration for Research Radar: the watchlists, topics, and tuning knobs.

The radar watches three kinds of stream — each STREAM becomes one OpenAlex
/works query:

  1. KEYWORDS — a phrase in the title/abstract (catches anyone who uses it).
  2. PEOPLE   — your watched researchers, all in ONE query (ids OR'd together).
  3. TOPICS   — one OpenAlex topic id each.

A stream is matched by an OpenAlex `filter` fragment (an author or topic id)
and/or a `search` phrase. `require` is an optional noise filter: if set, at
least one phrase must appear in the title/abstract or the paper is dropped.
"""

from dataclasses import dataclass, field


@dataclass
class Stream:
    key: str                      # short id, used in state + labels
    label: str                    # human-readable name shown in the digest
    filter: str = ""              # OpenAlex filter fragment, e.g. "author.id:A5065297243"
    search: str = ""              # title_and_abstract.search phrase
    require: list[str] = field(default_factory=list)  # if set, at least one must appear


# --- Watched researchers -----------------------------------------------------
# One flat list of everyone you follow — no categories. Following a researcher
# by OpenAlex author id is the equivalent of a Google Scholar "new articles"
# alert. The whole list becomes ONE OpenAlex query (ids OR'd together).
# The name/affiliation note is for your reference; only the id is sent.
# To find an id: https://api.openalex.org/authors?search=Their+Name
# (OpenAlex allows up to 50 ids OR'd in one filter; you have room to spare.)
PEOPLE = {
    "A5065297243": "Giancarlo Guizzardi (Twente) — UFO, OntoUML",
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
    "A5014287041": "Juan Sequeda (data.world) — knowledge graphs, semantic data",
    "A5075446663": "Frank Nack (Amsterdam) — interactive multimedia, semantic media",
    "A5050801999": "Panos Constantinides — digital innovation, information systems",
    "A5079338334": "Lucas Introna (Lancaster) — ethics & phenomenology of information systems",
    "A5060916131": "Paul A. L. Ducheine (Amsterdam/NLDA) — military law, cyber operations",
    "A5027932705": "Bernard Claverie (Bordeaux INP) — NATO cognitive warfare concept",
    "A5075868467": "Baptiste Prébot — Cognitive Warfare Index, CWDB",
    "A5138999954": "Maxime Audinet (IRSEM) — Russian influence, RT/Sputnik",
    "A5071977967": "Maxime Audinet (IRSEM) — second OpenAlex profile",
    "A5048734240": "Stefan Soesanto (ETH Zurich) — cyber conflict, information operations",
    "A5078972793": "Han Bouwmeester (NL Defence Academy) — maskirovka, reflexive control",
    "A5005470460": "Dima/Dmitry Adamsky (Reichman) — Russian strategic culture",
    "A5037734689": "Ofer Fridman (KCL) — Russian 'hybrid warfare'",
    "A5051215193": "Bettina Renz (Nottingham) — Russian military power",
    "A5092769843": "Jānis Bērziņš (Latvian NDA) — new generation warfare",
    "A5047539711": "Thomas Rid (Johns Hopkins SAIS) — active measures",
    "A5028631384": "Samuel Woolley (Pittsburgh) — computational propaganda",
    "A5045494255": "Kate Starbird (UW) — participatory disinformation",
    "A5085545989": "Yevgeniy Golovchenko (Copenhagen) — Russian disinformation",
    "A5026819080": "Martin Innes (Cardiff) — information operations in Europe",
    "A5073961643": "Sander van der Linden (Cambridge) — inoculation against misinformation",
    "A5017914184": "Stephan Lewandowsky (Bristol/Potsdam) — misinformation psychology",
    "A5036034260": "Vítor V. Vasconcelos (UvA) — collective behaviour, complexity",
    "A5021090586": "Michael (Mike) Lees (UvA) — complex-systems simulation",
}


# --- Topics ------------------------------------------------------------------
# Each OpenAlex topic becomes its own stream (one /works query per topic), so
# you can see which topic matched and prune a noisy one by deleting its line.
# Find a topic id at https://api.openalex.org/topics?search=Your+Topic+Name
# Topics split by how precise they are to your interests:
#   TOPICS       — narrow and on-theme: capture ≈ relevance, taken as-is.
#   GATED_TOPICS — relevant but broad: only kept when one of GATE_TERMS appears
#                  in the title/abstract (via the per-stream `require` filter),
#                  so a broad field is narrowed to the slice you care about.
# Broad, off-theme topics (general software-engineering methods, management,
# graph/DB/web/scientific-computing, GNNs, topic modelling, data management, …)
# were dropped: they scored high on quality but had nothing to do with you.
TOPICS = {
    # modelling / semantic-web cluster (also covers knowledge graphs & ontologies)
    "T10215": "Semantic Web and Ontologies",
    "T11450": "Model-Driven Software Engineering Techniques",
    "T10703": "Business Process Modeling and Analysis",
    # disinformation / security / military cluster (incl. hybrid threats)
    "T12221": "Cybersecurity and Cyber Warfare Studies",
    "T13369": "European and Russian Geopolitical Military Strategies",
    "T11147": "Misinformation and Its Impacts",
    "T14086": "Military and Defense Studies",
    "T12888": "Military Strategy and Technology",
    "T12957": "War, Ethics, and Justification",
    "T14432": "Freedom of Expression and Defamation",
    # ethics / reasoning cluster
    "T10883": "Ethics and Social Impacts of AI",
    "T11010": "Logic, Reasoning, and Knowledge",
}

# Relevant but broad: a paper is kept only if it also mentions one of GATE_TERMS.
GATED_TOPICS = {
    "T10749": "International Law and Human Rights",
    "T10994": "Terrorism, Counterterrorism, and Political Violence",
    "T11024": "Information Systems Theories and Implementation",
    "T12366": "Philosophy, Ethics, and Existentialism",
}

# Your cross-cutting terms. For a GATED_TOPIC, a paper is kept only if at least
# one appears in its title/abstract (matched as a lowercase substring, so
# "ontolog" also catches "ontology"/"ontologies" and "russia" catches "russian").
GATE_TERMS = [
    "disinformation", "misinformation", "propaganda", "influence operation",
    "information warfare", "information operation", "cognitive warfare",
    "hybrid warfare", "hybrid threat", "fimi", "reflexive control", "maskirovka",
    "cyber", "russia", "ontolog", "knowledge graph", "conceptual model",
    "semantic web",
]

# Name lookup across both sets (for the "captured because" explanation).
TOPIC_NAMES = {**TOPICS, **GATED_TOPICS}


def _authors(people: dict[str, str]) -> str:
    """Build an OpenAlex author.id filter fragment that ORs everyone together."""
    return "author.id:" + "|".join(people)


def author_name(author_id: str) -> str:
    """Just the person's name from a watchlist entry (drop affiliation/notes)."""
    desc = PEOPLE.get(author_id, "")
    if not desc:
        return author_id
    return desc.split(" (")[0].split(" — ")[0].strip()


def capture_reason(paper, stream) -> str:
    """Plain-language reason this paper entered the net: which filter matched."""
    if stream.search:
        return f'Matched the phrase "{stream.search}" in its title/abstract.'
    f = stream.filter or ""
    if f.startswith("topics.id:"):
        tid = f[len("topics.id:"):]
        return f"Tagged with your watched topic {TOPIC_NAMES.get(tid, tid)} ({tid})."
    if f.startswith("author.id:"):
        ids = set(f[len("author.id:"):].split("|"))
        hits = [author_name(a) for a in paper.author_ids if a in ids]
        who = ", ".join(dict.fromkeys(hits))  # dedupe, keep order
        if who:
            return f"Co-authored by {who}, on your watchlist."
        return f"From your watchlist: {stream.label}."
    return stream.label


def stream_kind(stream_key: str) -> str:
    """Which of the three kinds a stream belongs to: keyword / author / topic."""
    if stream_key.startswith("topic_"):
        return "topic"
    if stream_key == "people":
        return "author"
    return "keyword"


STREAMS: list[Stream] = [
    # --- 1. Keyword / term searches (a precise phrase in the title/abstract) -
    Stream(key="conceptual_modelling", label="Conceptual modelling (keyword)",
           search="conceptual modeling",
           require=["conceptual model", "conceptual modeling", "conceptual modelling"]),
    Stream(key="cognitive_warfare", label="Cognitive warfare (keyword)",
           search="cognitive warfare"),
    Stream(key="disinformation", label="Disinformation (keyword)",
           search="disinformation"),
    Stream(key="information_warfare", label="Information warfare (keyword)",
           search="information warfare"),
    Stream(key="influence_operations", label="Influence operations (keyword)",
           search="influence operations"),
    Stream(key="information_manipulation", label="Information manipulation / FIMI (keyword)",
           search="information manipulation"),
    Stream(key="fimi", label="FIMI (keyword)", search="FIMI"),
    Stream(key="reflexive_control", label="Reflexive control (keyword)",
           search="reflexive control"),
    Stream(key="hybrid_warfare", label="Hybrid warfare (keyword)",
           search="hybrid warfare"),
    Stream(key="ontouml", label="OntoUML (keyword)", search="OntoUML"),

    # --- 2. Watched researchers (all of PEOPLE in one query) ----------------
    Stream(key="people", label="Watched researchers", filter=_authors(PEOPLE)),
]

# --- 3. Topic streams: one per topic; GATED_TOPICS add the GATE_TERMS gate ---
STREAMS += [
    Stream(key=f"topic_{tid}", label=name, filter=f"topics.id:{tid}")
    for tid, name in TOPICS.items()
]
STREAMS += [
    Stream(key=f"topic_{tid}", label=name, filter=f"topics.id:{tid}", require=GATE_TERMS)
    for tid, name in GATED_TOPICS.items()
]

# === Tuning knobs ============================================================

# --- Fetch & ranking ---------------------------------------------------------
LOOKBACK_DAYS = 10   # how far back each run looks (margin over the cron cadence)
PER_PAGE = 50        # papers pulled per stream from OpenAlex (newest first)
MIN_SCORE = 1        # minimum quality score (relevance.py) to keep a paper

# Bonus when a paper trips more than one of your criteria (a watched author AND a
# watched topic, say): +MULTI_MATCH_BONUS per extra distinct criterion, capped at
# MULTI_MATCH_MAX. Set the bonus to 0 to rank on quality alone.
MULTI_MATCH_BONUS = 8
MULTI_MATCH_MAX = 24

# --- Report ------------------------------------------------------------------
# Drafts are chosen PER KIND (keywords / authors / topics), not globally, so a
# broad topic can't crowd out your people or key terms. Up to DRAFTS_PER_KIND
# full drafts from each kind (so at most 3 kinds × DRAFTS_PER_KIND per run); the
# rest go in the digest. Within the topic kind, PER_TOPIC_CAP spreads the picks
# across different topics instead of one busy one.
DRAFTS_PER_KIND = 3  # full LinkedIn drafts per kind (keywords / authors / topics)
PER_TOPIC_CAP = 2    # within topics, cap drafts from any single topic
DIGEST_MAX = 150     # max digest rows (keeps the GitHub issue under its 64k limit)

# --- Downloading PDFs (local `--download` runs only) -------------------------
# Every OPEN-ACCESS paper scoring >= DOWNLOAD_MIN_SCORE is saved to DOWNLOAD_DIR/
# (gitignored), up to DOWNLOAD_MAX per run. Closed-access papers are never
# downloaded (just listed in the digest, marked closed).
DOWNLOAD_MIN_SCORE = 70
DOWNLOAD_MAX = 50
DOWNLOAD_DIR = "papers"

# Preprints normally score below DOWNLOAD_MIN_SCORE, so they aren't saved. But in
# these areas the early work is worth having: a preprint is downloaded down to
# DOWNLOAD_PREPRINT_MIN_SCORE when its own primary topic is in PREPRINT_TOPICS, or
# the stream that caught it is in PREPRINT_STREAMS.
DOWNLOAD_PREPRINT_MIN_SCORE = 20
PREPRINT_TOPICS = {
    "T11147",   # Misinformation and Its Impacts      — disinformation
    "T10215",   # Semantic Web and Ontologies         — conceptual models
    "T11450",   # Model-Driven Software Engineering    — conceptual models
    "T12221",   # Cybersecurity and Cyber Warfare      — cognitive warfare
}
PREPRINT_STREAMS = {
    "conceptual_modelling",   # conceptual models
    "cognitive_warfare",      # cognitive warfare
}

# --- Reading list: most-cited papers (`python -m radar.main --canon`) --------
# A separate "impact" view: per topic, an all-time canon (by total citations) and
# a "rising" list of the last RISING_SINCE_YEARS (by citations-per-year, so newer
# breakouts aren't buried). Written to CANON_OUT; not drafted, not deduped.
# Keep it to a few core topics (ids must exist in TOPICS above).
CANON_TOPIC_IDS = [
    "T12221",   # Cybersecurity and Cyber Warfare Studies  (cognitive warfare)
    "T11147",   # Misinformation and Its Impacts           (disinformation)
    "T10215",   # Semantic Web and Ontologies              (conceptual models)
    "T11450",   # Model-Driven Software Engineering        (conceptual models)
]
CANON_PER_TOPIC = 10
RISING_PER_TOPIC = 10
RISING_SINCE_YEARS = 3
CANON_OUT = "state/reading_list.md"
