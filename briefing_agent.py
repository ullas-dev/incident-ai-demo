import os
from typing import Dict, List, Optional

try:
    import openai
except Exception:
    openai = None


def _template_brief(title, meeting_start_text, past_section):
    return f"""
Meeting Brief

Meeting: {title}
Start: {meeting_start_text}

What to know before this call:
- Review the latest decisions from the last few meetings.
- Confirm outstanding tasks and blockers.
- Keep the agenda focused on priority items.

Recent history:
{past_section}

Suggested prep:
- Read the last 2–3 meeting summaries.
- Identify any open items that need status updates.
- Prepare questions for unresolved issues.

Expected outcomes:
- Clear next actions with owners.
- Updated timeline for current work.
- Agreement on follow-up steps.
"""


def generate_brief(title: str, meeting_start: Optional[str], past_briefs: Optional[List[Dict]] = None) -> str:
    """Generate a meeting brief.

    If OPENAI_API_KEY is set and the OpenAI client is available, use the
    OpenAI ChatCompletion API to generate a polished brief. Otherwise fall
    back to the static template.
    """

    meeting_start_text = meeting_start or "Unknown start time"
    past_section = "No past notes available for this series."

    if past_briefs:
        past_lines = []
        for brief in past_briefs:
            start = brief.get("meeting_start", "Unknown")
            summary = brief.get("summary", "")
            first_line = summary.splitlines()[0] if summary else "No summary"
            past_lines.append(f"- {start}: {first_line}")

        past_section = "\n".join(past_lines)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or openai is None:
        return _template_brief(title, meeting_start_text, past_section)

    prompt = f"""
Create a concise, professional meeting brief.

Meeting title: {title}
Start: {meeting_start_text}
Recent history:
{past_section}

Produce a short meeting brief with key context, suggested prep, and expected outcomes.
Keep it under 250 words.
"""

    try:
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes meeting briefs."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.2,
        )
        text = response["choices"][0]["message"]["content"].strip()
        return text
    except Exception:
        return _template_brief(title, meeting_start_text, past_section)
