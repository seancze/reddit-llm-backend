from pydantic import BaseModel


class VoteRequest(BaseModel):
    query_id: str
    vote: int
