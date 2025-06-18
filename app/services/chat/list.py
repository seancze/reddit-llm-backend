from app.db.conn import MongoDBConnection
from app.db.get import get_user_chats
from app.schemas.chat_list_response import ChatListResponse
from typing import List


def chat_list(db_conn: MongoDBConnection, username: str) -> List[ChatListResponse]:
    user_chats = get_user_chats(db_conn, username)

    return user_chats
