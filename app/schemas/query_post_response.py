from pydantic import Field, field_validator
from bson import ObjectId
from typing import Literal
from app.schemas.message import Message
from app.schemas.role import BaseModelWithRoleEncoder
from app.schemas.custom_object_id import CustomObjectId


class QueryPostResponse(BaseModelWithRoleEncoder):
    response: list[Message]
    query_id: CustomObjectId = Field(default_factory=CustomObjectId)
    chat_id: CustomObjectId = Field(default_factory=CustomObjectId)
    user_vote: Literal[-1, 0, 1]

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }

    @field_validator("user_vote")
    @classmethod
    def check_user_vote(cls, v):
        if v not in [-1, 0, 1]:
            raise ValueError("user_vote must be -1, 0, or 1")
        return v
