from datetime import datetime
from agents import paper_analyzer, summary_generator, citation_extractor, key_insights
from agents.review_agent import run_with_review
from utils.logger import get_logger

logger = get_logger("boss_agent")

def run(paper_text: str) -> dict:
    """
    Boss Agent: orchestrates the full research analysis pipeline.
    Returns complete research brief dict.
    """
    logger.info("=" * 60)
    logger.info("BOSS AGENT: Starting research analysis pipeline")
    logger.info("=" * 60)

    state = {
        "paper_text": paper_text,
        "analysis": None,
        "summary": None,
        "citations": None,
        "insights": None,
        "review_scores": {},
        "retry_counts": {},
        "final_brief": None,
        "status": "running",
        "errors": []
    }

    # ── Step 1: Paper Analyzer ──────────────────────────────────────
    logger.info("BOSS: Delegating to Paper Analyzer Agent")
    try:
        analysis, review, attempts = run_with_review(
            "analysis", paper_analyzer.analyze, paper_text
        )
        state["analysis"] = analysis
        state["review_scores"]["analysis"] = review["score"]
        state["retry_counts"]["analysis"] = attempts
    except Exception as e:
        logger.error(f"BOSS: Paper Analyzer failed: {e}")
        state["errors"].append(f"Paper Analyzer: {e}")
        state["status"] = "failed"
        return state

    # ── Step 2: Summary Generator ───────────────────────────────────
    logger.info("BOSS: Delegating to Summary Generator Agent")
    try:
        summary, review, attempts = run_with_review(
            "summary",
            lambda pt, feedback="": summary_generator.generate(pt, state["analysis"], feedback=feedback),
            paper_text
        )
        state["summary"] = summary
        state["review_scores"]["summary"] = review["score"]
        state["retry_counts"]["summary"] = attempts
    except Exception as e:
        logger.error(f"BOSS: Summary Generator failed: {e}")
        state["errors"].append(f"Summary Generator: {e}")
        state["summary"] = {"summary": "Summary generation failed.", "word_count": 0}

    # ── Step 3: Citation Extractor ──────────────────────────────────
    logger.info("BOSS: Delegating to Citation Extractor Agent")
    try:
        citations, review, attempts = run_with_review(
            "citations", citation_extractor.extract, paper_text
        )
        state["citations"] = citations
        state["review_scores"]["citations"] = review["score"]
        state["retry_counts"]["citations"] = attempts
    except Exception as e:
        logger.error(f"BOSS: Citation Extractor failed: {e}")
        state["errors"].append(f"Citation Extractor: {e}")
        state["citations"] = {"total_count": 0, "citations": [], "key_related_works": []}

    # ── Step 4: Key Insights (Bonus) ────────────────────────────────
    logger.info("BOSS: Delegating to Key Insights Agent")
    try:
        insights, review, attempts = run_with_review(
            "insights",
            lambda pt, feedback="": key_insights.generate(pt, state["analysis"], feedback=feedback),
            paper_text
        )
        state["insights"] = insights
        state["review_scores"]["insights"] = review["score"]
        state["retry_counts"]["insights"] = attempts
    except Exception as e:
        logger.error(f"BOSS: Key Insights failed: {e}")
        state["errors"].append(f"Key Insights: {e}")
        state["insights"] = {"practical_takeaways": [], "field_implications": "N/A", "potential_applications": []}

    # ── Step 5: Combine into Final Brief ────────────────────────────
    logger.info("BOSS: Combining all outputs into final research brief")
    state["final_brief"] = _combine(state)
    state["status"] = "completed"

    avg_score = sum(state["review_scores"].values()) / max(len(state["review_scores"]), 1)
    logger.info(f"BOSS: Pipeline complete. Average quality score: {avg_score:.1f}/10")
    logger.info("=" * 60)

    return state


def _combine(state: dict) -> dict:
    """Combine all agent outputs into a single research brief."""
    analysis = state["analysis"] or {}
    summary = state["summary"] or {}
    citations = state["citations"] or {}
    insights = state["insights"] or {}

    return {
        "generated_at": datetime.now().isoformat(),
        "metadata": {
            "title": analysis.get("title", "Unknown"),
            "authors": analysis.get("authors", []),
            "year": analysis.get("year", "Unknown"),
            "venue": analysis.get("venue", "Unknown")
        },
        "research_analysis": {
            "problem_statement": analysis.get("problem_statement", ""),
            "hypothesis": analysis.get("hypothesis", ""),
            "methodology": analysis.get("methodology", ""),
            "experiments": analysis.get("experiments", ""),
            "key_findings": analysis.get("key_findings", []),
            "limitations": analysis.get("limitations", "")
        },
        "executive_summary": summary.get("summary", ""),
        "summary_word_count": summary.get("word_count", 0),
        "citations": {
            "total": citations.get("total_count", 0),
            "references": citations.get("citations", []),
            "key_related_works": citations.get("key_related_works", [])
        },
        "key_insights": {
            "takeaways": insights.get("practical_takeaways", []),
            "field_implications": insights.get("field_implications", ""),
            "applications": insights.get("potential_applications", []),
            "future_research": insights.get("future_research", ""),
            "who_should_read": insights.get("who_should_read", "")
        },
        "quality_report": {
            "scores": state["review_scores"],
            "retry_counts": state["retry_counts"],
            "average_score": round(
                sum(state["review_scores"].values()) / max(len(state["review_scores"]), 1), 1
            ),
            "errors": state["errors"]
        }
    }
