from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    comment: str

