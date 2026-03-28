"""
Test script for GitHub Actions.
Downloads a real arXiv paper and runs the full multi-agent pipeline.
Output saved to output_brief.json
"""

import json
import sys
from utils.pdf_parser import extract_text_from_url
from utils.llm_client import log_usage_summary
from agents.boss_agent import run
from utils.logger import get_logger

logger = get_logger("test")

# "Attention Is All You Need" - classic, clean PDF
SAMPLE_PAPER_URL = "https://arxiv.org/pdf/1706.03762"

def main():
    logger.info("=" * 60)
    logger.info("TEST: Research Paper Analyzer — Full Pipeline Run")
    logger.info(f"Paper: {SAMPLE_PAPER_URL}")
    logger.info("=" * 60)

    # Step 1: Extract text
    logger.info("Downloading and parsing PDF...")
    try:
        paper_text = extract_text_from_url(SAMPLE_PAPER_URL)
        logger.info(f"Extracted {len(paper_text)} characters")
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        sys.exit(1)

    # Step 2: Run pipeline
    logger.info("Starting multi-agent pipeline...")
    state = run(paper_text)

    if state["status"] == "failed":
        logger.error("Pipeline failed.")
        logger.error(f"Errors: {state.get('errors')}")
        sys.exit(1)

    brief = state["final_brief"]

    # Step 3: Print summary
    print("\n" + "=" * 60)
    print("RESEARCH BRIEF OUTPUT")
    print("=" * 60)
    print(f"Title:          {brief['metadata']['title']}")
    print(f"Authors:        {', '.join(brief['metadata']['authors'])}")
    print(f"Year:           {brief['metadata']['year']}")
    print(f"Venue:          {brief['metadata']['venue']}")
    print(f"\nExecutive Summary:\n{brief['executive_summary']}")
    print(f"\nKey Findings:")
    for f in brief['research_analysis']['key_findings']:
        print(f"  • {f}")
    print(f"\nKey Insights:")
    for t in brief['key_insights']['takeaways']:
        print(f"  → {t}")
    print(f"\nCitations found: {brief['citations']['total']}")
    print(f"\nQuality Scores:  {brief['quality_report']['scores']}")
    print(f"Average Score:   {brief['quality_report']['average_score']}/10")
    print("=" * 60)

    # Step 4: Save to file (uploaded as GitHub Actions artifact)
    with open("output_brief.json", "w") as f:
        json.dump(brief, f, indent=2)
    logger.info("Full brief saved to output_brief.json")
    log_usage_summary()
    logger.info("TEST PASSED ✓")

if __name__ == "__main__":
    main()
