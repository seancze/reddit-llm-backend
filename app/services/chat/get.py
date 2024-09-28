from app.db.conn import MongoDBConnection
from app.db.get import get_chat_by_id
from app.schemas.query_get_response import QueryGetResponse
from fastapi import HTTPException
from typing import Optional


def chat_get(
    db_conn: MongoDBConnection, chat_id: str, username: Optional[str]
) -> QueryGetResponse:
    chat_obj = get_chat_by_id(db_conn, chat_id, username)
    if chat_obj is None:
        raise HTTPException(status_code=404, detail="Query not found")

    last_query = chat_obj["queries"][-1]
    return QueryGetResponse(
        response=chat_obj["messages"],
        query_id=last_query["_id"],
        chat_id=chat_id,
        user_vote=last_query.get("user_vote", 0),
        is_chat_owner=last_query["is_chat_owner"],
    )
