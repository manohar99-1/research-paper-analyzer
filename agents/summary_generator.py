import json
from utils.llm_client import call_llm
from utils.logger import get_logger

logger = get_logger("summary_generator")

SYSTEM_PROMPT = """You are an expert scientific writer who creates clear, concise executive summaries 
of academic research papers for busy professionals. 
Always respond with valid JSON only. No preamble, no explanation outside the JSON."""

def generate(paper_text: str, analysis: dict, feedback: str = "") -> dict:
    """
    Generate a 150-200 word executive summary of the research paper.
    Returns dict with summary and word count.
    """
    feedback_section = f"\n\nPrevious review feedback to address:\n{feedback}" if feedback else ""

    user_prompt = f"""Write a clear executive summary of this research paper.

Paper Analysis Context:
- Title: {analysis.get('title', 'Unknown')}
- Problem: {analysis.get('problem_statement', '')}
- Methodology: {analysis.get('methodology', '')}
- Key Findings: {', '.join(analysis.get('key_findings', []))}

Return ONLY a valid JSON object:
{{
  "summary": "150-200 word executive summary covering: (1) problem being solved, (2) approach taken, (3) key results, (4) significance of the findings. Write in plain English for non-specialists.",
  "word_count": <integer word count of the summary>
}}
{feedback_section}

Full Paper Text (for additional context):
{paper_text[:4000]}"""

    logger.info("Summary Generator Agent running...")
    raw = call_llm(SYSTEM_PROMPT, user_prompt)

    try:
        result = _parse_json(raw)
        logger.info(f"Summary generated ({result.get('word_count', '?')} words)")
        return result
    except Exception as e:
        logger.error(f"JSON parse failed: {e}")
        raise ValueError(f"Summary Generator returned invalid JSON: {e}")


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
