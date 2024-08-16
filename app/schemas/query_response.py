from pydantic import BaseModel, Field
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    # allows PyObjectId to be created from a string, bytes, or an existing ObjectId
    # during serialisation (e.g. to JSON), this helps to convert the ObjectId to a string
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return core_schema.union_schema(
            [
                core_schema.str_schema(),
                core_schema.bytes_schema(),
                core_schema.is_instance_schema(ObjectId),
            ],
            serialization=core_schema.to_string_ser_schema(),
        )


class QueryResponse(BaseModel):
    response: str
    query_id: PyObjectId = Field(default_factory=PyObjectId)

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }
