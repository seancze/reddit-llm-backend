from app.db.conn import MongoDBConnection
from app.db.get import get_query_by_id
from app.schemas.query_get_response import QueryGetResponse
from fastapi import HTTPException
from typing import Optional


def query_get(
    db_conn: MongoDBConnection, query_id: str, username: Optional[str]
) -> QueryGetResponse:
    query_doc = get_query_by_id(db_conn, query_id, username)
    if query_doc is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return QueryGetResponse(
        query=query_doc["query"],
        response=query_doc["response"],
        query_id=query_doc["_id"],
        user_vote=query_doc.get("user_vote", 0),
    )
