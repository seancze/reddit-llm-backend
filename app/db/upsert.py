import time
from app.db.conn import MongoDBConnection
from app.constants import CACHE_DURATION
from bson import ObjectId


def upsert_query_document(query_doc: dict, db_conn: MongoDBConnection):
    used_cache = query_doc.get("used_cache", False)
    updated_utc = query_doc["updated_utc"]
    query_collection = db_conn.get_collection("query")
    query = query_doc["query"]

    if used_cache:
        # find the existing document by "_id" and update only "updated_utc" and "query_count"
        query_collection.update_one(
            {"_id": query_doc["_id"]},
            {"$set": {"updated_utc": updated_utc}, "$inc": {"query_count": 1}},
        )
    else:
        prev_time = updated_utc - CACHE_DURATION

        query_collection.update_one(
            {"query": query, "created_utc": {"$gte": prev_time}},
            {
                "$set": query_doc,
                "$setOnInsert": {"created_utc": updated_utc},
            },
            upsert=True,
        )


def update_query_vote(query_id: str, vote: int, db_conn: MongoDBConnection):
    query_collection = db_conn.get_collection("query")
    updated_utc = int(time.time())

    update_data = {
        "$set": {"updated_utc": updated_utc, "vote": vote},
    }

    result = query_collection.update_one({"_id": ObjectId(query_id)}, update_data)

    return result
