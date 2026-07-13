from fastapi import FastAPI

from database import init_db, get_upcoming_briefs, get_open_actions

app = FastAPI()


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home():
    return {
        "message": "Meeting Assistant"
    }


@app.get("/briefs/upcoming")
def upcoming_briefs(hours: int = 24):
    return get_upcoming_briefs(hours)


@app.get("/actions/open")
def open_actions():
    return get_open_actions()
