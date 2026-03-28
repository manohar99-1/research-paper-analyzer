"""
CLI runner for Research Paper Analyzer.
Usage:
  python main.py --pdf path/to/paper.pdf
  python main.py --url https://arxiv.org/pdf/xxxx.pdf
  python main.py --text "paste paper text here"
"""

import argparse
import json
import sys
from utils.pdf_parser import extract_text_from_file, extract_text_from_url
from agents.boss_agent import run
from utils.logger import get_logger

logger = get_logger("main")


def main():
    parser = argparse.ArgumentParser(description="AI-Powered Research Paper Analyzer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdf", help="Path to local PDF file")
    group.add_argument("--url", help="URL to PDF file")
    group.add_argument("--text", help="Raw paper text")
    parser.add_argument("--output", help="Save output to JSON file", default=None)

    args = parser.parse_args()

    # Extract paper text
    if args.pdf:
        logger.info(f"Loading PDF: {args.pdf}")
        paper_text = extract_text_from_file(args.pdf)
    elif args.url:
        logger.info(f"Downloading PDF: {args.url}")
        paper_text = extract_text_from_url(args.url)
    else:
        paper_text = args.text

    if not paper_text or len(paper_text.strip()) < 100:
        logger.error("Paper text is too short or empty.")
        sys.exit(1)

    logger.info(f"Paper text loaded ({len(paper_text)} chars). Starting analysis...")

    # Run pipeline
    state = run(paper_text)

    if state["status"] == "failed":
        logger.error("Pipeline failed.")
        sys.exit(1)

    brief = state["final_brief"]

    # Print summary to console
    print("\n" + "=" * 60)
    print("RESEARCH BRIEF")
    print("=" * 60)
    print(f"Title:   {brief['metadata']['title']}")
    print(f"Authors: {', '.join(brief['metadata']['authors'])}")
    print(f"Year:    {brief['metadata']['year']}")
    print(f"\nExecutive Summary:\n{brief['executive_summary']}")
    print(f"\nKey Findings:")
    for f in brief['research_analysis']['key_findings']:
        print(f"  • {f}")
    print(f"\nCitations: {brief['citations']['total']} references found")
    print(f"\nQuality Scores: {brief['quality_report']['scores']}")
    print(f"Average Score: {brief['quality_report']['average_score']}/10")
    print("=" * 60)

    # Save to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(brief, f, indent=2)
        logger.info(f"Full brief saved to: {args.output}")
    else:
        print("\nFull JSON output:")
        print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    main()
