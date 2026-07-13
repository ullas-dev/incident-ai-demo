from calendar_client import get_upcoming_meetings
from briefing_agent import generate_brief
from gmail_client import get_unread_messages, get_email_body
from action_agent import extract_actions
from database import (
    get_or_create_series,
    brief_exists,
    save_brief,
    save_action,
    note_processed,
    get_past_briefs,
)


def calendar_trigger():

    meetings = get_upcoming_meetings(window_minutes=15)

    for meeting in meetings:
        series_id = get_or_create_series(
            meeting["series_key"],
            meeting["summary"],
            meeting.get("description")
        )

        if brief_exists(series_id, meeting["start"]):
            continue

        past_briefs = get_past_briefs(series_id)
        summary = generate_brief(
            meeting["summary"],
            meeting["start"],
            past_briefs
        )

        save_brief(
            series_id,
            meeting["start"],
            summary
        )

        print(f"Brief generated for meeting '{meeting['summary']}' starting at {meeting['start']}.")


def gmail_trigger():

    messages = get_unread_messages()

    for message in messages:
        message_id = message["id"]

        if note_processed(message_id):
            continue

        body = get_email_body(message_id)
        actions = extract_actions(body)

        if not actions:
            print(f"No actions extracted from message {message_id}.")
            continue

        for action in actions:
            save_action(
                action["owner"],
                action["task"],
                action["due_date"],
                source_note=message_id
            )
            print(f"Action saved for owner {action['owner']}: {action['task']}")


if __name__ == "__main__":
    calendar_trigger()
    gmail_trigger()