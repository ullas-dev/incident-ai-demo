from gmail_client import (
    get_unread_messages,
    get_email_body
)

messages = get_unread_messages()

print(f"Unread emails: {len(messages)}")

if messages:

    body = get_email_body(
        messages[0]["id"]
    )

    print("\nEMAIL:\n")
    print(body)