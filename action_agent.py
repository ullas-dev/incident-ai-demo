import json
import os
import re
from typing import Dict, List

try:
    import openai
except Exception:
    openai = None


def _template_extract_actions(text: str) -> List[Dict]:
    actions = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        owner = "Unassigned"
        task = line
        due_date = None

        if ":" in line:
            owner_part, task_part = line.split(":", 1)
            owner = owner_part.strip() or owner
            task = task_part.strip()

        due_match = re.search(r"(?:due|by)\s+([^,.;]+)", task, re.IGNORECASE)
        if due_match:
            due_date = due_match.group(1).strip()

        if not due_date:
            due_date = "Next Week"

        actions.append(
            {
                "owner": owner,
                "task": task,
                "due_date": due_date
            }
        )

    return actions


def extract_actions(text: str) -> List[Dict]:
    """Extract action items from text.

    If OPENAI_API_KEY is available, use OpenAI to parse action items. Otherwise
    fall back to the simple regex-based extractor.
    """

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or openai is None:
        return _template_extract_actions(text)

    prompt = f"""
Extract action items from the following note. For each action, return it as a JSON array of objects with keys: owner, task, due_date.

Note:
{text}

If no explicit due date is present, set due_date to 'Next Week'. If no owner is present, set owner to 'Unassigned'.
"""

    try:
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": "You are a parser that extracts action items from text and returns valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.0,
        )
        text_response = response["choices"][0]["message"]["content"].strip()
        parsed = json.loads(text_response)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass

    return _template_extract_actions(text)