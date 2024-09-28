from pydantic import BaseModel
from enum import Enum


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class BaseModelWithRoleEncoder(BaseModel):
    class Config:
        json_encoders = {Role: lambda v: v.value}
