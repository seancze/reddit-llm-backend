import time
from app.db.conn import MongoDBConnection
from app.constants import CACHE_DURATION
from bson import ObjectId


def upsert_query_document(db_conn: MongoDBConnection, query_doc: dict, username: str):
    query_collection = db_conn.get_collection("query")
    used_cache = query_doc.get("used_cache", False)
    updated_utc = query_doc["updated_utc"]
    query = query_doc["query"]

    if used_cache:
        query_collection.update_one(
            {"_id": query_doc["_id"]},
            {"$set": {"updated_utc": updated_utc}, "$inc": {"query_count": 1}},
        )
    else:
        # even though this looks like an upsert operation
        # at this stage, the query document should not exist
        # so it is acting more like an insert operation
        prev_time = updated_utc - CACHE_DURATION
        query_collection.update_one(
            {"query": query, "created_utc": {"$gte": prev_time}},
            {
                "$set": query_doc,
                "$setOnInsert": {"created_utc": updated_utc, "username": username},
                "$inc": {"query_count": 1},
            },
            upsert=True,
        )


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
