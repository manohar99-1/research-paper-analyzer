import os
import time
import requests
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger("llm_client")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Free models in priority order — best quality first
# Each has ~20 req/min and 200 req/day on free tier
FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",      # best quality, use first
    "meta-llama/llama-3.1-8b-instruct:free",        # proven reliable, fast
    "mistralai/mistral-7b-instruct:free",            # fallback
    "qwen/qwen2.5-72b-instruct:free",               # last resort
]

# Track per-model usage to avoid hitting rate limits
_model_state = {
    model: {
        "requests_this_minute": 0,
        "minute_start": time.time(),
        "total_requests": 0,
        "last_429_at": 0,
        "failures": 0,
    }
    for model in FREE_MODELS
}

RPM_LIMIT = 18      # stay under 20 req/min (buffer of 2)
RPD_LIMIT = 190     # stay under 200 req/day (buffer of 10)
COOLDOWN_AFTER_429 = 60  # seconds before retrying a rate-limited model


def _reset_minute_counter(state: dict):
    now = time.time()
    if now - state["minute_start"] >= 60:
        state["requests_this_minute"] = 0
        state["minute_start"] = now


def _pick_model():
    for model in FREE_MODELS:
        state = _model_state[model]
        _reset_minute_counter(state)

        if state["total_requests"] >= RPD_LIMIT:
            logger.warning(f"[{model}] Day limit reached, skipping")
            continue

        if state["requests_this_minute"] >= RPM_LIMIT:
            logger.warning(f"[{model}] Minute limit reached, skipping")
            continue

        if time.time() - state["last_429_at"] < COOLDOWN_AFTER_429:
            remaining = int(COOLDOWN_AFTER_429 - (time.time() - state["last_429_at"]))
            logger.warning(f"[{model}] In cooldown ({remaining}s left), skipping")
            continue

        if state["failures"] >= 3:
            logger.warning(f"[{model}] Too many failures, skipping")
            continue

        return model

    return None


def call_llm(system_prompt: str, user_prompt: str, max_retries: int = 3, temperature: float = 0.3) -> str:
    """
    Call OpenRouter with multi-model fallback and rate limit tracking.
    Models tried in order: llama-3.3-70b → llama-3.1-8b → mistral-7b → qwen-72b
    Automatically switches model on 429, 404, or repeated failures.
    """
    if not OPENROUTER_API_KEY:
        raise EnvironmentError("OPENROUTER_API_KEY not set in .env")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/manohar99-1/research-paper-analyzer",
        "X-Title": "Research Paper Analyzer"
    }

    global_attempts = 0
    max_global_attempts = len(FREE_MODELS) * max_retries

    while global_attempts < max_global_attempts:
        model = _pick_model()

        if model is None:
            logger.warning("All models at rate limit. Waiting 30s...")
            time.sleep(30)
            for state in _model_state.values():
                state["requests_this_minute"] = 0
                state["minute_start"] = time.time()
            global_attempts += 1
            continue

        state = _model_state[model]
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 2000
        }

        try:
            logger.debug(f"Calling [{model.split('/')[-1]}] rpm:{state['requests_this_minute']} total:{state['total_requests']}")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

            state["requests_this_minute"] += 1
            state["total_requests"] += 1

            if response.status_code == 429:
                logger.warning(f"[{model.split('/')[-1]}] Rate limited. Cooling down {COOLDOWN_AFTER_429}s.")
                state["last_429_at"] = time.time()
                state["failures"] += 1
                global_attempts += 1
                continue

            if response.status_code == 404:
                logger.error(f"[{model.split('/')[-1]}] Not found (404). Blacklisting.")
                state["failures"] = 99
                global_attempts += 1
                continue

            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            state["failures"] = 0
            logger.debug(f"[{model.split('/')[-1]}] OK ({len(content)} chars)")
            return content.strip()

        except requests.exceptions.Timeout:
            logger.error(f"[{model.split('/')[-1]}] Timeout.")
            state["failures"] += 1
            global_attempts += 1
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            logger.error(f"[{model.split('/')[-1]}] Error: {e}")
            state["failures"] += 1
            global_attempts += 1
            time.sleep(2)

        except (KeyError, IndexError) as e:
            logger.error(f"[{model.split('/')[-1]}] Bad response format: {e}")
            state["failures"] += 1
            global_attempts += 1

    raise RuntimeError("All models failed after exhausting all retries.")


def log_usage_summary():
    logger.info("── Model Usage Summary ──")
    for model, state in _model_state.items():
        short = model.split("/")[-1]
        logger.info(f"  {short}: total={state['total_requests']}, rpm={state['requests_this_minute']}, failures={state['failures']}")
