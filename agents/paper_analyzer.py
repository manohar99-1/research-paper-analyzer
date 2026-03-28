import json
from utils.llm_client import call_llm
from utils.logger import get_logger

logger = get_logger("paper_analyzer")

SYSTEM_PROMPT = """You are an expert academic research analyst. Your job is to deeply analyze 
research papers and extract structured information with precision and clarity.
Always respond with valid JSON only. No preamble, no explanation outside the JSON."""

def analyze(paper_text: str, feedback: str = "") -> dict:
    """
    Extract methodology, hypothesis, experiments, and key findings from paper.
    Returns structured dict.
    """
    feedback_section = f"\n\nPrevious review feedback to address:\n{feedback}" if feedback else ""

    user_prompt = f"""Analyze this research paper and extract the following information.
Return ONLY a valid JSON object with these exact keys:

{{
  "title": "paper title or 'Unknown' if not found",
  "authors": ["author1", "author2"],
  "year": "publication year or 'Unknown'",
  "venue": "journal or conference name or 'Unknown'",
  "problem_statement": "what problem does this paper solve? (2-3 sentences)",
  "hypothesis": "the main hypothesis or research question (1-2 sentences)",
  "methodology": "the approach and methods used (3-5 sentences)",
  "experiments": "what experiments or studies were conducted (2-4 sentences)",
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "limitations": "any limitations mentioned (1-2 sentences or 'Not mentioned')"
}}
{feedback_section}

Research Paper:
{paper_text}"""

    logger.info("Paper Analyzer Agent running...")
    raw = call_llm(SYSTEM_PROMPT, user_prompt)

    try:
        result = _parse_json(raw)
        logger.info("Paper analysis complete")
        return result
    except Exception as e:
        logger.error(f"JSON parse failed: {e}. Raw: {raw[:200]}")
        raise ValueError(f"Paper Analyzer returned invalid JSON: {e}")


def _parse_json(text: str) -> dict:
    """Strip markdown fences and parse JSON."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
