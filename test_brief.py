from calendar_client import get_events
from briefing_agent import generate_brief
from database import save_brief

events = get_events()

for event in events:

    summary = generate_brief(
        event["summary"]
    )

    save_brief(
        event["summary"],
        summary
    )

    print(summary)

print("Brief saved to database.")