import time
from app.db.conn import MongoDBConnection
from app.constants import CACHE_DURATION
from app.utils.format_utils import get_human_readable_datetime


def get_cached_response(query: str, db_conn: MongoDBConnection):
    query_collection = db_conn.get_collection("query")

    prev_time = int(time.time()) - CACHE_DURATION

    # check if a document with the same query has been made recently
    search_query = {"query": query, "created_utc": {"$gte": prev_time}}

    existing_doc = query_collection.find_one(
        search_query, {"response": 1, "_id": 1, "is_error": 1}
    )

    # this means that the query has been made recently so we get the cached response
    if existing_doc:
        return existing_doc

    # simply return None instaed of raising an exception to allow a response to be generated for this query
    return None


def get_response_from_pipeline(
    collection_name: str, pipeline: list, db_conn: MongoDBConnection
):
    collection = db_conn.get_collection(collection_name)

    if collection_name == "thread":
        # add a $project stage to exclude selftext_embedding at the beginning of the pipeline
        pipeline.insert(0, {"$project": {"selftext_embedding": 0, "_id": 0}})

    # execute the aggregation pipeline
    documents = list(collection.aggregate(pipeline))
    if documents and "created_utc" in documents[0]:
        for doc in documents:
            doc["created_date"] = get_human_readable_datetime(doc["created_utc"])
            del doc["created_utc"]

    return documents
