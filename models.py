from pydantic import BaseModel


class ActionItem(BaseModel):

    task: str
    owner: str
    due_date: str
    status: str