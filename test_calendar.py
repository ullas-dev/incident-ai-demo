from calendar_client import get_events

events = get_events()

print(f"Events found: {len(events)}")

for event in events:

    print("Meeting:", event["summary"])

    print(
        "Start:",
        event["start"]
    )

    print("----------------")