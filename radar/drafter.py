"""Turn a paper into a LinkedIn post draft: a clean template from its metadata.

No API, no cost — you write the one-line take and post it yourself.
"""

from __future__ import annotations

import textwrap

from .openalex import Paper

DEFAULT_TAGS = "#Research #AcademicResearch #OpenAlex"

# Hashtags per stream key. Anything not listed (incl. most topic streams) falls
# back to DEFAULT_TAGS.
HASHTAGS = {
    "conceptual_modelling": "#ConceptualModeling #DataModeling #Ontology",
    "cognitive_warfare": "#CognitiveWarfare #InformationWarfare #CognitiveSecurity",
    # Researcher watchlists
    "favourites": "#Research #KnowledgeGraphs #Ontology",
    "cogwar_people": "#CognitiveWarfare #InformationWarfare #CognitiveSecurity",
    "russia_people": "#RussiaStudies #HybridWarfare #StrategicStudies",
    "disinfo_people": "#Disinformation #InformationIntegrity #MediaLiteracy",
    "onto_people": "#Ontology #KnowledgeGraph #SemanticWeb",
    "complexity_people": "#ComplexSystems #ComplexityScience #ComputationalSocialScience",
    # A few high-traffic topic streams get tailored tags; the rest use DEFAULT.
    "topic_T10215": "#SemanticWeb #KnowledgeGraph #LinkedData",
    "topic_T11450": "#ModelDrivenEngineering #MDE #ConceptualModeling",
    "topic_T11147": "#Disinformation #InformationIntegrity #MediaLiteracy",
    "topic_T12221": "#Cybersecurity #CyberWarfare #InfoSec",
    "topic_T13369": "#RussiaStudies #Geopolitics #StrategicStudies",
}


def _trim(text: str, words: int = 55) -> str:
    parts = text.split()
    return " ".join(parts[:words]) + ("…" if len(parts) > words else "")


def make_draft(paper: Paper) -> str:
    authors = ", ".join(paper.authors[:3]) + (" et al." if len(paper.authors) > 3 else "")
    venue = f" ({paper.venue})" if paper.venue else ""
    summary = _trim(paper.abstract) if paper.abstract else "New paper worth a look."
    tags = HASHTAGS.get(paper.stream, DEFAULT_TAGS)
    return textwrap.dedent(f"""\
        \U0001F4C4 New paper: "{paper.title}"
        {authors}{venue} — {paper.date}

        {summary}

        Why it matters: [add your one-line take here]

        \U0001F517 {paper.url}

        {tags}""").rstrip()
