"""Turn a paper into a LinkedIn post draft.

Default: a clean template built from the paper's metadata -- no API, no cost.
Optional: if ANTHROPIC_API_KEY is set, polish the draft with Claude for a more
natural voice. The template fallback always runs if the API call fails.
"""

from __future__ import annotations

import os
import textwrap

from .openalex import Paper

MODEL = "claude-sonnet-5-5"

# Hashtags per stream key. Topic streams (key "topic_T…") and anything missing
# fall back to DEFAULT_TAGS.
DEFAULT_TAGS = "#Research #AcademicResearch #OpenAlex"

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


def template_draft(paper: Paper) -> str:
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


def claude_draft(paper: Paper) -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
    except ImportError:
        return None

    prompt = (
        "Write a concise, engaging LinkedIn post (120-160 words) about this new "
        "academic paper for an audience of researchers and practitioners. "
        "Lead with why it matters, plain language, no hype, first person optional. "
        "End with the link and 3 relevant hashtags. Leave a bracketed "
        "[add your take] placeholder for one personal sentence.\n\n"
        f"Title: {paper.title}\n"
        f"Authors: {', '.join(paper.authors[:6])}\n"
        f"Venue: {paper.venue}\nDate: {paper.date}\n"
        f"Link: {paper.url}\n"
        f"Abstract: {paper.abstract[:1500]}"
    )
    try:
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return None


def make_draft(paper: Paper) -> str:
    return claude_draft(paper) or template_draft(paper)
