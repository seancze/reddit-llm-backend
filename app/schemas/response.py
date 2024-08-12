from pydantic import BaseModel
from typing import Optional


class Response(BaseModel):
    response: str
    data: Optional[list]
