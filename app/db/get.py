from app.db.conn import MongoDBConnection
from app.utils.format_utils import get_human_readable_datetime
from bson import ObjectId
from typing import Optional, List
from app.schemas.role import Role
from app.schemas.message import Message
from app.schemas.chat_list_response import ChatListResponse
from pymongo.collection import Collection


def get_user_chats(
    db_conn: MongoDBConnection,
    username: str,
    page: int = 0,
) -> List[ChatListResponse]:
    """
    Return the first query document of each unique chat by this user.
    Paginates the results, returning at most 25 chats per page.
    """
    query_collection: Collection = db_conn.get_collection("query")
    LIMIT = 25

    pipeline = [
        # find all chats that are created by the user and NOT deleted
        {"$match": {"username": username, "is_deleted": {"$ne": True}}},
        # this sort ensures that $first in the stage below retrieves the earliest query of each chat
        {"$sort": {"created_utc": 1}},
        {
            "$group": {
                "_id": "$chat_id",
                "query": {"$first": "$query"},
                "created_utc": {"$first": "$created_utc"},
            }
        },
        {"$project": {"_id": 0, "chat_id": "$_id", "query": 1, "created_utc": 1}},
        # this sort ensures that the list of chats retrieved are sorted in descending order
        {"$sort": {"created_utc": -1}},
        {"$skip": page * LIMIT},
        {"$limit": LIMIT},
    ]

    first_queries = list(query_collection.aggregate(pipeline))

    return first_queries


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

    existing_docs = list(
        query_collection.find(
            {
                "chat_id": object_id,
                # this will match documents where
                # (A) "is_deleted" does not exist
                # (B) "is_deleted" exists and is False
                "is_deleted": {"$ne": True},
            },
            fields,
        ).sort("created_utc", 1)
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


def get_response_from_pipeline(
    db_conn: MongoDBConnection, collection_name: str, pipeline: list
):
    print(f"[INFO] Getting MongoDB pipeline response...")
    collection = db_conn.get_collection(collection_name)

    if collection_name == "thread":
        # add a $project stage to exclude selftext_embedding at the beginning of the pipeline
        pipeline.insert(0, {"$project": {"selftext_embedding": 0, "_id": 0}})

    # TODO: make subreddit a parameter
    pipeline.insert(0, {"$match": {"subreddit": "sgexams"}})

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
    for doc in documents:
        if "created_utc" in doc:
            doc["created_date"] = get_human_readable_datetime(doc["created_utc"])
            del doc["created_utc"]
        else:
            # if one doc does not have "created_utc", all docs will not have "created_utc"
            break

    return documents


def get_thread_metadata_and_top_comments(
    db_conn: MongoDBConnection, vector_search_result: list
):
    search_result = ""
    similar_threads = []

    for i, result in enumerate(vector_search_result):
        title = result.get("title")
        url = f"https://reddit.com{result.get('permalink')}"
        score = result.get("score")
        # skip if any of the fields above are None
        if not (score and url):
            continue
        # if title is None, use part of the url as the title
        # NOTE: we allow title to be None because this field does not exist in the comment schema
        if not title:
            # get the 2nd last part of the url
            # e.g. https://reddit.com/r/sgexams/comments/123456/placeholder_url_slug_that_we_will_be_using/123456/
            url_formatted = url.split("/")[-3]
            # e.g. title = "Placeholder Url Slug That We Will Be Using"
            title = url_formatted.replace("_", " ").title()
        selftext = result.get("selftext", "N/A")
        selftext_ls = selftext.split()
        # only get top 500 words
        if len(selftext_ls) > 500:
            selftext = " ".join(selftext_ls[:500]) + "..."

        similar_threads.append((f"[{title}]({url}) (Upvotes: {score})", score))

        search_result += f"""Thread {i+1} (Score: {score})\nTitle: {title}\nURL: {url}\nBody: {selftext}\n\n\n"""
        # print(f"search_result: {search_result}")

    return search_result, similar_threads


def _format_query_doc(query_doc, username: str):
    # extract the vote for the specific username
    # if the user has not voted, the default vote is 0
    user_vote = query_doc.get("votes", {}).get(username, 0)

    doc_username = query_doc.pop("username", None)
    query_doc["is_chat_owner"] = doc_username == username

    # add the user's vote to the returned document
    query_doc["user_vote"] = user_vote

    return query_doc
