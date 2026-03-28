# Troubleshooting Guide

## Common Issues and Solutions

### 1. "All models failed. Check your OPENROUTER_API_KEY" Error

This error occurs when all free models return 404 errors. This happens when:

#### Solution 1: Update to Latest Free Models

The free tier models on OpenRouter change frequently. The code has been updated to use:
```python
FREE_MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
]
```

**To verify current free models:**
1. Visit https://openrouter.ai/models?order=newest&supported_parameters=tools&max_price=0
2. Filter by: `Free` in pricing
3. Update `utils/llm_client.py` with currently available model names

#### Solution 2: Check Your API Key
```bash
# Verify your .env file exists
cat .env

# Should contain:
OPENROUTER_API_KEY=sk-or-v1-...
```

**Get a new API key:**
1. Go to https://openrouter.ai/keys
2. Sign in (or create account)
3. Click "Create Key"
4. Copy the key (starts with `sk-or-v1-`)
5. Paste into `.env` file

#### Solution 3: Test API Key Manually
```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -d '{
    "model": "meta-llama/llama-3.2-3b-instruct:free",
    "messages": [{"role": "user", "content": "Say hi"}]
  }'
```

Expected response: JSON with `choices[0].message.content`

---

### 2. GitHub Actions Failure

If the test is failing in GitHub Actions:

#### Solution: Add API Key to GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `OPENROUTER_API_KEY`
5. Value: Your OpenRouter API key
6. Click **Add secret**

#### Update `.github/workflows/test_pipeline.yml`:
```yaml
env:
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

---

### 3. Rate Limiting (429 Errors)

Free tier has strict rate limits:
- **20 requests per minute** per model
- **200 requests per day** across all models

#### Solution: Implement Backoff

The code already handles this automatically:
- Waits 60 seconds on 429
- Retries same model once
- Falls back to next model if still rate-limited

**If you hit limits frequently:**
1. Reduce paper length: `MAX_CHARS = 8000` in `utils/pdf_parser.py`
2. Use fewer retries: `max_retries=2` in agent calls
3. Wait 5-10 minutes between runs

---

### 4. PDF Parsing Failures

#### Symptoms:
- "Extracted 0 characters from PDF"
- Analysis returns empty results

#### Solutions:

**For scanned PDFs:**
```bash
pip install pytesseract pillow pdf2image
# Then update pdf_parser.py to use OCR
```

**For protected PDFs:**
```bash
# Remove password protection first
qpdf --decrypt --password=PASSWORD input.pdf output.pdf
```

**For image-based PDFs:**
Use OCR tools or provide direct text input instead.

---

### 5. Mobile Phone Deployment (Replit/Vercel)

Since you're working from mobile:

#### Option 1: Replit (Recommended for Mobile)

1. Fork the GitHub repo to Replit
2. In Replit Secrets (🔒 icon), add:
   - Key: `OPENROUTER_API_KEY`
   - Value: Your API key
3. Click **Run** button
4. Access the web UI at the provided URL

#### Option 2: Render.com (Free Tier)

1. Connect your GitHub repo
2. Create a **Web Service**
3. Build command: `pip install -r requirements.txt`
4. Start command: `python app.py`
5. Add environment variable: `OPENROUTER_API_KEY`

---

### 6. Assignment Submission Checklist

For the Vilambo assignment (deadline: March 28, 2026):

- [x] Multi-agent system with Boss Agent ✓
- [x] Sub-Agents with specialized tasks ✓
- [x] Automated quality control (Review Agent) ✓
- [ ] **Public GitHub repository** (check visibility)
- [ ] **Live URL** (Replit/Render/Vercel)
- [ ] **Demo video** (3 minutes max)
  - Show: File upload → Processing → Results display
  - Use screen recorder on phone (AZ Screen Recorder, etc.)
  - Upload to Google Drive (make public)

#### Quick Demo Video Script:
```
[0:00-0:30] Introduction
"Hi, I'm Manohar. This is my AI Research Paper Analyzer built for Vilambo."

[0:30-1:00] Architecture Overview
[Show README diagram]
"It uses a Boss Agent that coordinates 4 specialized sub-agents with quality control."

[1:00-2:00] Live Demo
[Open web UI, upload paper, show processing]
"Here I'm uploading the 'Attention Is All You Need' paper..."
[Wait for results]

[2:00-2:30] Results Walkthrough
[Show analysis, summary, citations, insights]
"The system extracted methodology, generated a summary, and identified key insights."

[2:30-3:00] Technical Details
"Built with Python, Flask, OpenRouter API, and pure multi-agent orchestration - no LangChain."
```

---

### 7. Quick Fixes for Common Errors

#### Import Error: `No module named 'pdfplumber'`
```bash
pip install -r requirements.txt
```

#### Port Already in Use
```bash
# Kill existing Flask process
pkill -f app.py

# Or use different port
export FLASK_PORT=8000
python app.py
```

#### CORS Errors in Browser
Already handled in `app.py` with:
```python
CORS(app, resources={r"/*": {"origins": "*"}})
```

If still occurring, open `frontend/index.html` with **Live Server** or serve it:
```bash
python -m http.server 8080
# Then open http://localhost:8080/frontend/
```

---

### 8. Alternative: Switch to Groq API (Faster, Free)

If OpenRouter continues to have issues:
```bash
pip install groq
```

**Update `utils/llm_client.py`:**
```python
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(system_prompt, user_prompt, **kwargs):
    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=2000
    )
    return response.choices[0].message.content
```

Get free Groq API key: https://console.groq.com/keys

---

## Still Having Issues?

1. **Check logs:** Look for `[ERROR]` lines in console output
2. **Test individual components:**
```bash
   python -c "from utils.llm_client import call_llm; print(call_llm('You are helpful', 'Say hi'))"
```
3. **Verify API key format:** Should start with `sk-or-v1-` for OpenRouter
4. **Check internet connection:** Required for API calls
5. **Review OpenRouter dashboard:** https://openrouter.ai/activity

---

**Last Updated:** March 28, 2026
