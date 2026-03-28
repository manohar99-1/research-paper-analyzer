# Research Paper Analyzer 🔬

An AI-powered multi-agent system that automatically analyzes academic research papers — extracting methodology, generating executive summaries, organizing citations, and producing actionable insights with automated quality control.

Built for the Vilambo AI Agent Developer Intern assignment.

---

## Agent Architecture

```
Input: PDF / URL / Text
          │
          ▼
┌─────────────────────────────────────┐
│          BOSS AGENT                 │
│  Orchestrates the entire pipeline   │
│  Delegates tasks to sub-agents      │
│  Combines all outputs into brief    │
└─────────┬───────────────────────────┘
          │
          ▼
┌─────────────────────┐
│  Paper Analyzer     │──► Review Agent (score/10, retry if <7, max 2x)
│  Sub-Agent          │
└─────────┬───────────┘
          │ (if approved)
          ▼
┌──────────────────────────────────────────────────────┐
│  Summary Generator  │  Citation Extractor  │  Key    │
│  Sub-Agent          │  Sub-Agent           │ Insights│
│        │            │         │            │  Agent  │
│        ▼            │         ▼            │    │    │
│  Review Agent       │  Review Agent        │ Review  │
│  (score, retry)     │  (score, retry)      │ Agent   │
└──────────────────────────────────────────────────────┘
          │ (all approved)
          ▼
┌─────────────────────────────────────┐
│  Boss Agent: Final Combine          │
│  Complete Research Brief (JSON)     │
└─────────┬───────────────────────────┘
          │
          ▼
     HTML Frontend
```

### Agents

| Agent | Role | Output |
|-------|------|--------|
| **Boss Agent** | Orchestrator — delegates tasks, combines outputs | Final research brief |
| **Paper Analyzer** | Extracts title, authors, methodology, experiments, findings | Structured JSON |
| **Summary Generator** | 150-200 word executive summary | Summary + word count |
| **Citation Extractor** | All references and key related works | Citations list |
| **Key Insights** | Practical takeaways, applications, future research | Insights list |
| **Review Agent** | Scores each output 1-10, triggers retry if score < 7, max 2 retries | Score + feedback |

---

## Tech Stack

- **Orchestration**: Custom Python pipeline (no LangChain/CrewAI boilerplate — pure agent design)
- **LLM**: OpenRouter API (free tier — `mistralai/mistral-7b-instruct:free` by default)
- **PDF Parsing**: `pdfplumber`
- **API**: Flask + CORS
- **Frontend**: Vanilla HTML/CSS/JS (no dependencies)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/manohar99-1/research-paper-analyzer
cd research-paper-analyzer
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:

```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
```

Get a free API key at [openrouter.ai](https://openrouter.ai).

---

## Usage

### CLI

```bash
# Analyze a local PDF
python main.py --pdf paper.pdf

# Analyze from arXiv URL
python main.py --url https://arxiv.org/pdf/2310.06825.pdf

# Save output to file
python main.py --pdf paper.pdf --output brief.json

# Analyze raw text
python main.py --text "Abstract: This paper proposes..."
```

### Flask API

```bash
python app.py
```

API runs on `http://localhost:5000`

**Endpoints:**

```
POST /analyze/pdf     multipart/form-data, key: "file"
POST /analyze/url     JSON: {"url": "https://..."}
POST /analyze/text    JSON: {"text": "full paper text"}
GET  /health          health check
```

### Web UI

Open `frontend/index.html` in your browser. Make sure the Flask server is running first.

---

## Output Format

```json
{
  "metadata": {
    "title": "Paper Title",
    "authors": ["Author 1", "Author 2"],
    "year": "2024",
    "venue": "NeurIPS"
  },
  "research_analysis": {
    "problem_statement": "...",
    "hypothesis": "...",
    "methodology": "...",
    "experiments": "...",
    "key_findings": ["finding 1", "finding 2"],
    "limitations": "..."
  },
  "executive_summary": "150-200 word summary...",
  "citations": {
    "total": 42,
    "references": [...],
    "key_related_works": [...]
  },
  "key_insights": {
    "takeaways": [...],
    "field_implications": "...",
    "applications": [...],
    "future_research": "...",
    "who_should_read": "..."
  },
  "quality_report": {
    "scores": {"analysis": 8, "summary": 9, "citations": 7, "insights": 8},
    "average_score": 8.0,
    "retry_counts": {"analysis": 1, ...},
    "errors": []
  }
}
```

---

## Project Structure

```
research-paper-analyzer/
├── agents/
│   ├── boss_agent.py         # Main orchestrator
│   ├── paper_analyzer.py     # Methodology & findings extraction
│   ├── summary_generator.py  # Executive summary (150-200 words)
│   ├── citation_extractor.py # Reference extraction
│   ├── key_insights.py       # Actionable takeaways
│   └── review_agent.py       # Quality scoring + retry logic
├── utils/
│   ├── llm_client.py         # OpenRouter API wrapper + retry
│   ├── pdf_parser.py         # pdfplumber text extraction
│   └── logger.py             # Structured logging
├── frontend/
│   └── index.html            # Web UI
├── app.py                    # Flask REST API
├── main.py                   # CLI runner
├── requirements.txt
├── .env.example
└── README.md
```

---

## Review & Quality Control

The Review Agent evaluates every sub-agent output:

- **Score ≥ 7**: Output approved, pipeline continues
- **Score < 7**: Agent re-runs with specific feedback (max 2 retries)
- **After 2 retries**: Best available output is used, flagged in quality report

This prevents infinite loops while ensuring quality improvement.

---

## Known Limitations

- Very long papers (>12,000 chars) are truncated to fit context windows
- Free-tier LLM models may produce lower quality than GPT-4o-mini
- PDF parsing may struggle with scanned or image-based papers
- Rate limits on free OpenRouter tier may slow down processing

---

## Sample Input

Any arXiv paper works well. Example:
- https://arxiv.org/pdf/1706.03762.pdf (Attention Is All You Need)
- https://arxiv.org/pdf/2310.06825.pdf (Mistral 7B)

---

Built by Manohar Poleboina · [GitHub](https://github.com/manohar99-1)
