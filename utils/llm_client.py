import os
import time
import requests
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger("llm_client")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Models in priority order — falls back to next on 404/failure
# Updated March 2026 - verified working free models
FREE_MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
]

# Per-model state
_model_state = {
    model: {
        "requests_this_minute": 0,
        "minute_start": time.time(),
        "total_requests": 0,
        "last_429_at": 0,
        "blacklisted": False,   # permanent skip after 404
    }
    for model in FREE_MODELS
}

RPM_LIMIT = 18
COOLDOWN_AFTER_429 = 60


def _reset_minute(state):
    if time.time() - state["minute_start"] >= 60:
        state["requests_this_minute"] = 0
        state["minute_start"] = time.time()


def call_llm(system_prompt: str, user_prompt: str, max_retries: int = 3, temperature: float = 0.3) -> str:
    """
    Call OpenRouter with multi-model fallback.
    Tries each model once before moving to next.
    Fails fast on 404 (blacklists model permanently).
    Waits on 429 then retries same model once, then moves on.
    """
    if not OPENROUTER_API_KEY:
        raise EnvironmentError("OPENROUTER_API_KEY not set in .env")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/manohar99-1/research-paper-analyzer",
        "X-Title": "Research Paper Analyzer"
    }

    for model in FREE_MODELS:
        state = _model_state[model]

        if state["blacklisted"]:
            continue

        _reset_minute(state)

        # If rate limited recently, wait once then try
        if time.time() - state["last_429_at"] < COOLDOWN_AFTER_429:
            wait = COOLDOWN_AFTER_429 - int(time.time() - state["last_429_at"])
            logger.warning(f"[{model.split('/')[-1]}] Rate limited, waiting {wait}s...")
            time.sleep(wait)

        # Try this model up to max_retries times
        for attempt in range(1, max_retries + 1):
            _reset_minute(state)

            if state["requests_this_minute"] >= RPM_LIMIT:
                logger.warning(f"[{model.split('/')[-1]}] RPM limit hit, moving to next model")
                break

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
                logger.debug(f"[{model.split('/')[-1]}] Attempt {attempt}/{max_retries}")
                response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

                state["requests_this_minute"] += 1
                state["total_requests"] += 1

                if response.status_code == 429:
                    logger.warning(f"[{model.split('/')[-1]}] 429 rate limited. Waiting {COOLDOWN_AFTER_429}s...")
                    state["last_429_at"] = time.time()
                    time.sleep(COOLDOWN_AFTER_429)
                    continue  # retry same model after wait

                if response.status_code == 404:
                    logger.error(f"[{model.split('/')[-1]}] 404 not found. Blacklisting, trying next model.")
                    state["blacklisted"] = True
                    break  # move to next model immediately

                if response.status_code == 401:
                    raise EnvironmentError("Invalid OPENROUTER_API_KEY — check your secret.")

                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                logger.info(f"[{model.split('/')[-1]}] Success ({len(content)} chars)")
                return content.strip()

            except EnvironmentError:
                raise

            except requests.exceptions.Timeout:
                logger.error(f"[{model.split('/')[-1]}] Timeout on attempt {attempt}")
                time.sleep(2)

            except requests.exceptions.RequestException as e:
                logger.error(f"[{model.split('/')[-1]}] Error: {e}")
                time.sleep(2)

            except (KeyError, IndexError) as e:
                logger.error(f"[{model.split('/')[-1]}] Bad response format: {e}")
                break  # malformed response, try next model

    raise RuntimeError("All models failed. Check your OPENROUTER_API_KEY and model availability.")


def log_usage_summary():
    logger.info("── Model Usage Summary ──")
    for model, state in _model_state.items():
        short = model.split("/")[-1]
        status = "BLACKLISTED" if state["blacklisted"] else "ok"
        logger.info(f"  {short}: total={state['total_requests']}, rpm={state['requests_this_minute']}, status={status}")
