from app.db.conn import MongoDBConnection
from app.db.upsert import delete_chat_by_id
from fastapi import HTTPException


def chat_delete(
    db_conn: MongoDBConnection,
    chat_id: str,
) -> int:
    deleted_count = delete_chat_by_id(db_conn, chat_id)
    if deleted_count is None:
        raise HTTPException(status_code=404, detail="Query not found")

    return deleted_count
