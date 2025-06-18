from pydantic import BaseModel, Field
from app.schemas.custom_object_id import CustomObjectId


class ChatListResponse(BaseModel):
    chat_id: CustomObjectId = Field(default_factory=CustomObjectId)
    query: str
    created_utc: int
