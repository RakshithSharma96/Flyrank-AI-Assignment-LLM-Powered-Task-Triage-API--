import json
import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, APIStatusError, APITimeoutError

load_dotenv()

PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "prompts"
    / "triage-v1.md"
)

LOG_PATH = (
    Path(__file__).resolve().parent.parent
    / "logs"
    / "cost.jsonl"
)

MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]
TIMEOUT_SECONDS = 30.0


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def get_client() -> OpenAI:
    return OpenAI(
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
        timeout=TIMEOUT_SECONDS,
        max_retries=0,
    )


def log_cost(
    prompt_tokens,
    completion_tokens,
    duration_ms,
    repair_count,
):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "prompt_version": "triage-v1",
        "model": os.getenv("LLM_MODEL"),
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "duration_ms": duration_ms,
        "repair_count": repair_count,
    }

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def call_llm(messages, repair_count=0):
    client = get_client()

    for attempt in range(MAX_RETRIES + 1):
        start = time.perf_counter()

        try:
            response = client.chat.completions.create(
                model=os.getenv("LLM_MODEL"),
                messages=messages,
                temperature=0.0,
            )

            duration_ms = round(
                (time.perf_counter() - start) * 1000
            )

            usage = response.usage

            log_cost(
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
                duration_ms=duration_ms,
                repair_count=repair_count,
            )

            return response.choices[0].message.content

        except APITimeoutError:
            if attempt >= MAX_RETRIES:
                raise

        except APIStatusError as error:
            status_code = error.status_code

            if status_code not in {429, 500, 502, 503, 504}:
                raise

            if attempt >= MAX_RETRIES:
                raise

            retry_after = None

            if status_code == 429:
                headers = getattr(error, "response", None)
                if headers is not None:
                    retry_after = headers.headers.get("retry-after")

            if retry_after is not None:
                delay = float(retry_after)
            else:
                delay = BACKOFF_SECONDS[attempt]

            delay += random.uniform(0, 0.25)
            time.sleep(delay)

    raise RuntimeError("LLM retry loop exited unexpectedly.")


def classify_task(text: str):
    prompt = load_prompt()

    return call_llm(
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        repair_count=0,
    )


def repair_task(
    text: str,
    broken_output: str,
    validation_error: str,
):
    prompt = load_prompt()

    repair_message = f"""
The previous model output was invalid.

Original user input:
{text}

Broken model output:
{broken_output}

Validation error:
{validation_error}

Return a corrected response that follows the exact JSON output shape and all rules from the system prompt.

Return JSON only.
Do not explain the correction.
"""

    return call_llm(
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": repair_message,
            },
        ],
        repair_count=1,
    )