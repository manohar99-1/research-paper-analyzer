import os
import time
import requests
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger("llm_client")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_llm(system_prompt: str, user_prompt: str, max_retries: int = 3, temperature: float = 0.3) -> str:
    """
    Call OpenRouter LLM with retry logic and error handling.
    Returns the model's text response.
    """
    if not OPENROUTER_API_KEY:
        raise EnvironmentError("OPENROUTER_API_KEY not set in .env")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/manohar99-1/research-paper-analyzer",
        "X-Title": "Research Paper Analyzer"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 2000
    }

    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"LLM call attempt {attempt}/{max_retries} using model: {OPENROUTER_MODEL}")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

            if response.status_code == 429:
                wait = 2 ** attempt
                logger.warning(f"Rate limited. Waiting {wait}s before retry...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.debug(f"LLM responded successfully ({len(content)} chars)")
            return content.strip()

        except requests.exceptions.Timeout:
            logger.error(f"Attempt {attempt}: Request timed out.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Attempt {attempt}: Request error: {e}")
        except (KeyError, IndexError) as e:
            logger.error(f"Attempt {attempt}: Unexpected response format: {e}")

        if attempt < max_retries:
            time.sleep(2)

    raise RuntimeError(f"LLM call failed after {max_retries} attempts.")
