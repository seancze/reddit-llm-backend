import time
from app.db.conn import MongoDBConnection
from app.constants import CACHE_DURATION
from app.utils.format_utils import get_human_readable_datetime
from bson import ObjectId
from typing import Optional
from app.schemas.role import Role
from app.schemas.message import Message


def get_chat_by_id(db_conn: MongoDBConnection, chat_id: str, username: Optional[str]):
    query_collection = db_conn.get_collection("query")

    try:
        object_id = ObjectId(chat_id)
    except:
        # return None if the id is invalid
        return None

    # find all documents by chat_id and sort by created_utc
    fields = {
        "query": 1,
        "response": 1,
        "_id": 1,
        "is_error": 1,
        "created_utc": 1,
        "username": 1,
    }
    if username is not None:
        fields[f"votes.{username}"] = 1

    existing_docs = query_collection.find({"chat_id": object_id}, fields).sort(
        "created_utc", 1
    )

    if existing_docs:
        formatted_docs = []
        messages = []
        for doc in existing_docs:
            formatted_docs.append(_format_query_doc(doc, username))
            messages.extend(
                [
                    Message(content=doc["query"], role=Role.USER),
                    Message(content=doc["response"], role=Role.ASSISTANT),
                ]
            )
        return {
            "messages": messages,
            "queries": formatted_docs,
        }

    # return None to allow the service to generate a 404 response (i.e. for better separation of concerns)
    return None


def get_query_by_id(db_conn: MongoDBConnection, query_id: str, username: Optional[str]):
    query_collection = db_conn.get_collection("query")

    try:
        object_id = ObjectId(query_id)
    except:
        # return None if the id is invalid
        return None

    # find the document by its _id
    fields = {"query": 1, "response": 1, "_id": 1, "is_error": 1}
    if username is not None:
        fields[f"votes.{username}"] = 1
    existing_doc = query_collection.find_one({"_id": object_id}, fields)

    if existing_doc:
        return _format_query_doc(existing_doc, username)

    # return None to allow the service to generate a 404 response (i.e. for better separation of concerns)
    return None


def get_cached_response(db_conn: MongoDBConnection, query: str, username: str):
    query_collection = db_conn.get_collection("query")

    prev_time = int(time.time()) - CACHE_DURATION

    # check if a document with the same query has been made recently
    search_query = {"query": query, "created_utc": {"$gte": prev_time}}

    existing_doc = query_collection.find_one(
        search_query, {"response": 1, "_id": 1, "is_error": 1, f"votes.{username}": 1}
    )

    # this means that the query has been made recently so we get the cached response
    if existing_doc:
        return _format_query_doc(existing_doc, username)

    # simply return None instead of raising an exception to allow a response to be generated for this query
    return None


def get_response_from_pipeline(
    db_conn: MongoDBConnection, collection_name: str, pipeline: list
):
    collection = db_conn.get_collection(collection_name)

    if collection_name == "thread":
        # add a $project stage to exclude selftext_embedding at the beginning of the pipeline
        pipeline.insert(0, {"$project": {"selftext_embedding": 0, "_id": 0}})

    # check if $limit stage exists in the pipeline
    limit_index = next(
        (i for i, stage in enumerate(pipeline) if "$limit" in stage), None
    )

    if limit_index is not None:
        # if $limit exists, update it to be at most 10
        original_limit = pipeline[limit_index]["$limit"]
        pipeline[limit_index]["$limit"] = min(10, original_limit)
    else:
        # if $limit doesn't exist, add it to the end of the pipeline
        pipeline.append({"$limit": 10})

    # execute the aggregation pipeline
    documents = list(collection.aggregate(pipeline))
    if documents and "created_utc" in documents[0]:
        for doc in documents:
            doc["created_date"] = get_human_readable_datetime(doc["created_utc"])
            del doc["created_utc"]

    return documents


def _format_query_doc(query_doc, username: str):
    # extract the vote for the specific username
    # if the user has not voted, the default vote is 0
    user_vote = query_doc.get("votes", {}).get(username, 0)

    doc_username = query_doc.pop("username", None)
    query_doc["is_chat_owner"] = doc_username == username

    # add the user's vote to the returned document
    query_doc["user_vote"] = user_vote

    return query_doc
