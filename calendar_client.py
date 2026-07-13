from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
from datetime import datetime, timedelta, timezone

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly"
]


def get_calendar_service():

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            try:
                creds = flow.run_local_server(port=0)
            except Exception:
                creds = flow.run_console()

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build(
        "calendar",
        "v3",
        credentials=creds
    )


def get_upcoming_meetings(window_minutes=15):

    service = get_calendar_service()

    now = datetime.now(timezone.utc)
    end_time = now + timedelta(minutes=window_minutes)

    events = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=end_time.isoformat(),
        maxResults=20,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    meetings = []
    for event in events.get("items", []):
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        meetings.append({
            "id": event.get("id"),
            "series_key": event.get("recurringEventId") or event.get("id"),
            "summary": event.get("summary", "Untitled meeting"),
            "description": event.get("description"),
            "start": start,
        })

    return meetings


def get_events():
    return get_upcoming_meetings()
