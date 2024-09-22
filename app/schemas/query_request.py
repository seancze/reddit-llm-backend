from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
