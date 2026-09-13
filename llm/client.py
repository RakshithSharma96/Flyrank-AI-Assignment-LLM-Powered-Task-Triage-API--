import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "prompts"
    / "triage-v1.md"
)


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def get_client() -> OpenAI:
    return OpenAI(
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
    )


def classify_task(text: str):
    client = get_client()
    prompt = load_prompt()

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
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
        temperature=0.0,
    )

    return response.choices[0].message.content


def repair_task(
    text: str,
    broken_output: str,
    validation_error: str,
):
    client = get_client()
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

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
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
        temperature=0.0,
    )

    return response.choices[0].message.content