import json
from utils.llm_client import call_llm
from utils.logger import get_logger

logger = get_logger("citation_extractor")

SYSTEM_PROMPT = """You are an expert at extracting and organizing academic citations and references 
from research papers. Extract every reference mentioned in the text.
Always respond with valid JSON only. No preamble, no explanation outside the JSON."""

def extract(paper_text: str, feedback: str = "") -> dict:
    """
    Extract and organize all citations and references from the paper.
    Returns structured dict with citations list.
    """
    feedback_section = f"\n\nPrevious review feedback to address:\n{feedback}" if feedback else ""

    user_prompt = f"""Extract all citations and references from this research paper.

Return ONLY a valid JSON object:
{{
  "total_count": <integer>,
  "citations": [
    {{
      "index": 1,
      "authors": "author names as they appear",
      "title": "paper/book title",
      "year": "year or 'Unknown'",
      "venue": "journal, conference, or publisher or 'Unknown'"
    }}
  ],
  "key_related_works": ["brief description of 3-5 most important cited works and why they matter"]
}}

Extract from the References/Bibliography section primarily. If no formal references section exists,
extract inline citations. Include ALL references found.
{feedback_section}

Paper Text:
{paper_text}"""

    logger.info("Citation Extractor Agent running...")
    raw = call_llm(SYSTEM_PROMPT, user_prompt)

    try:
        result = _parse_json(raw)
        logger.info(f"Extracted {result.get('total_count', '?')} citations")
        return result
    except Exception as e:
        logger.error(f"JSON parse failed: {e}")
        raise ValueError(f"Citation Extractor returned invalid JSON: {e}")


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
