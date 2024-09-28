import time
from app.db.conn import MongoDBConnection
from bson import ObjectId


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
