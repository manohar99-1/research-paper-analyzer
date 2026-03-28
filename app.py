"""
Flask API for Research Paper Analyzer.
Endpoints:
  POST /analyze/pdf   - upload PDF file
  POST /analyze/url   - analyze from URL
  POST /analyze/text  - analyze raw text
  GET  /health        - health check
"""

import os
import json
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from utils.pdf_parser import extract_text_from_file, extract_text_from_url
from agents.boss_agent import run
from utils.logger import get_logger

load_dotenv()
logger = get_logger("app")

app = Flask(__name__)
CORS(app)

MAX_TEXT_LENGTH = 50000


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Research Paper Analyzer"})


@app.route("/analyze/pdf", methods=["POST"])
def analyze_pdf():
    """Upload a PDF file and analyze it."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Send PDF as multipart/form-data with key 'file'"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "File must be a PDF"}), 400

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        logger.info(f"Received PDF: {file.filename}")
        paper_text = extract_text_from_file(tmp_path)
        os.unlink(tmp_path)

        return _run_pipeline(paper_text)

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        logger.error(f"PDF analysis error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/analyze/url", methods=["POST"])
def analyze_url():
    """Analyze a paper from a PDF URL."""
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Send JSON with 'url' key"}), 400

    url = data["url"].strip()
    if not url.startswith("http"):
        return jsonify({"error": "Invalid URL"}), 400

    try:
        logger.info(f"Received URL: {url}")
        paper_text = extract_text_from_url(url)
        return _run_pipeline(paper_text)

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        logger.error(f"URL analysis error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/analyze/text", methods=["POST"])
def analyze_text():
    """Analyze raw paper text."""
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Send JSON with 'text' key"}), 400

    paper_text = data["text"].strip()
    if len(paper_text) < 100:
        return jsonify({"error": "Text too short. Minimum 100 characters."}), 400

    if len(paper_text) > MAX_TEXT_LENGTH:
        paper_text = paper_text[:MAX_TEXT_LENGTH]
        logger.warning("Text truncated to max length")

    return _run_pipeline(paper_text)


def _run_pipeline(paper_text: str):
    """Run the agent pipeline and return JSON response."""
    if not paper_text or len(paper_text.strip()) < 100:
        return jsonify({"error": "Could not extract sufficient text from paper"}), 422

    state = run(paper_text)

    if state["status"] == "failed":
        return jsonify({
            "error": "Pipeline failed",
            "details": state.get("errors", [])
        }), 500

    return jsonify({
        "status": "success",
        "brief": state["final_brief"]
    })


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
