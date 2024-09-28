from typing import Optional
from app.schemas.message import Message
from app.schemas.role import BaseModelWithRoleEncoder


class QueryRequest(BaseModelWithRoleEncoder):
    query: list[Message]
    chat_id: Optional[str] = None
