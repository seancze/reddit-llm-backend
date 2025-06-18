import time
from app.db.conn import MongoDBConnection
from bson import ObjectId
from typing import Optional


def insert_query_document(db_conn: MongoDBConnection, query_doc: dict, username: str):
    query_collection = db_conn.get_collection("query")
    updated_utc = query_doc["updated_utc"]
    query_doc["username"] = username
    query_doc["created_utc"] = updated_utc
    query_doc["query_count"] = 1
    query_collection.insert_one(query_doc)


def update_query_vote(
    db_conn: MongoDBConnection, query_id: str, vote: int, username: str
):
    query_collection = db_conn.get_collection("query")
    updated_utc = int(time.time())

    update_data = {
        "$set": {"updated_utc": updated_utc, f"votes.{username}": vote},
    }

    result = query_collection.update_one({"_id": ObjectId(query_id)}, update_data)

    return result


def update_query_count(db_conn: MongoDBConnection, query_id: str):
    query_collection = db_conn.get_collection("query")
    updated_utc = int(time.time())

    update_data = {
        "$set": {"updated_utc": updated_utc},
        "$inc": {"query_count": 1},
    }

    result = query_collection.update_one({"_id": ObjectId(query_id)}, update_data)

    return result


def delete_chat_by_id(db_conn: MongoDBConnection, chat_id: str) -> Optional[int]:
    query_collection = db_conn.get_collection("query")

    try:
        object_id = ObjectId(chat_id)
    except Exception as e:
        print(f"[WARNING] Invalid chat_id in delete_chat_by_id(): {e}")
        # invalid id
        return None

    result = query_collection.update_many(
        {"chat_id": object_id}, {"$set": {"is_deleted": True}}
    )
    # result.modified_count is how many docs got the new field or had it flipped to True
    # in other words, the number of queries that got deleted
    return result.modified_count
