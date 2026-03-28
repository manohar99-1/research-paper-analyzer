import json
from utils.llm_client import call_llm
from utils.logger import get_logger

logger = get_logger("key_insights")

SYSTEM_PROMPT = """You are a strategic research analyst who identifies practical implications 
and actionable insights from academic research for practitioners and decision-makers.
Always respond with valid JSON only. No preamble, no explanation outside the JSON."""

def generate(paper_text: str, analysis: dict, feedback: str = "") -> dict:
    """
    Generate actionable key insights and practical takeaways from the paper.
    Returns structured dict with insights.
    """
    feedback_section = f"\n\nPrevious review feedback to address:\n{feedback}" if feedback else ""

    user_prompt = f"""Based on this research paper, generate practical insights and takeaways.

Paper Context:
- Title: {analysis.get('title', 'Unknown')}
- Key Findings: {', '.join(analysis.get('key_findings', []))}
- Methodology: {analysis.get('methodology', '')}

Return ONLY a valid JSON object:
{{
  "practical_takeaways": [
    "actionable takeaway 1",
    "actionable takeaway 2",
    "actionable takeaway 3"
  ],
  "field_implications": "how does this research impact or advance the field? (2-3 sentences)",
  "potential_applications": [
    "real-world application 1",
    "real-world application 2"
  ],
  "future_research": "what future work does this paper suggest? (1-2 sentences)",
  "who_should_read": "who benefits most from reading this paper? (1 sentence)"
}}
{feedback_section}

Paper Text (for context):
{paper_text[:3000]}"""

    logger.info("Key Insights Agent running...")
    raw = call_llm(SYSTEM_PROMPT, user_prompt)

    try:
        result = _parse_json(raw)
        logger.info("Key insights generated")
        return result
    except Exception as e:
        logger.error(f"JSON parse failed: {e}")
        raise ValueError(f"Key Insights Agent returned invalid JSON: {e}")


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
