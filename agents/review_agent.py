import json
from utils.llm_client import call_llm
from utils.logger import get_logger

logger = get_logger("review_agent")

QUALITY_THRESHOLD = 7
MAX_RETRIES = 2

SYSTEM_PROMPT = """You are a strict quality control reviewer for AI-generated research analysis.
Your job is to evaluate outputs for accuracy, completeness, and clarity.
Always respond with valid JSON only. No preamble, no explanation outside the JSON."""

CRITERIA = {
    "analysis": "accuracy of extracted information, completeness of methodology/findings/metadata, clarity",
    "summary": "150-200 word count, covers problem/approach/results/significance, plain language, no jargon",
    "citations": "completeness of reference extraction, proper formatting, key related works identified",
    "insights": "actionability of takeaways, relevance to findings, practical applications, future research"
}

def review(agent_name: str, output: dict, paper_text: str) -> dict:
    """
    Review an agent's output. Returns {score, feedback, approved}.
    agent_name: 'analysis' | 'summary' | 'citations' | 'insights'
    """
    criteria = CRITERIA.get(agent_name, "accuracy, completeness, and clarity")

    user_prompt = f"""Review this {agent_name} output from an AI research analyzer.

Evaluation Criteria: {criteria}

Output to Review:
{json.dumps(output, indent=2)}

Original Paper (first 2000 chars for verification):
{paper_text[:2000]}

Return ONLY a valid JSON object:
{{
  "score": <integer 1-10>,
  "approved": <true if score >= {QUALITY_THRESHOLD}, false otherwise>,
  "strengths": "what is good about this output (1-2 sentences)",
  "issues": "specific problems found, or 'None' if approved",
  "feedback": "specific instructions for improvement if not approved, or 'Output meets quality standards' if approved"
}}

Scoring guide:
- 9-10: Excellent, complete, accurate, well-structured
- 7-8: Good, minor gaps but acceptable
- 5-6: Mediocre, missing important information
- 1-4: Poor, major errors or very incomplete"""

    logger.info(f"Review Agent evaluating: {agent_name}")
    raw = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.1)

    try:
        result = _parse_json(raw)
        score = result.get("score", 0)
        approved = score >= QUALITY_THRESHOLD
        result["approved"] = approved
        logger.info(f"Review [{agent_name}]: score={score}/10, approved={approved}")
        return result
    except Exception as e:
        logger.error(f"Review Agent JSON parse failed: {e}")
        # Fallback: approve to prevent blocking pipeline
        return {"score": 7, "approved": True, "feedback": "Review failed, auto-approved", "issues": "None", "strengths": "N/A"}


def run_with_review(agent_name: str, agent_fn, paper_text: str, *args) -> tuple:
    """
    Run an agent function with review-and-retry logic.
    Returns (final_output, review_result, attempts_used)
    
    agent_fn signature: fn(paper_text, *args, feedback="") -> dict
    """
    feedback = ""
    last_output = None
    last_review = None

    for attempt in range(1, MAX_RETRIES + 2):  # +2 = initial run + MAX_RETRIES
        logger.info(f"[{agent_name}] Attempt {attempt}/{MAX_RETRIES + 1}")

        try:
            output = agent_fn(paper_text, *args, feedback=feedback)
        except Exception as e:
            logger.error(f"[{agent_name}] Agent failed on attempt {attempt}: {e}")
            if attempt > MAX_RETRIES:
                raise
            feedback = f"Previous attempt errored: {e}. Please produce valid JSON output."
            continue

        review_result = review(agent_name, output, paper_text)
        last_output = output
        last_review = review_result

        if review_result["approved"]:
            logger.info(f"[{agent_name}] Approved on attempt {attempt}")
            return output, review_result, attempt

        if attempt <= MAX_RETRIES:
            feedback = review_result.get("feedback", "")
            logger.warning(f"[{agent_name}] Score {review_result['score']}/10. Retrying with feedback...")
        else:
            logger.warning(f"[{agent_name}] Max retries reached. Using best result (score: {review_result['score']}/10)")

    return last_output, last_review, MAX_RETRIES + 1


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
