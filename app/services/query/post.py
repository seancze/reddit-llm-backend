import time
from copy import deepcopy
from bson import ObjectId
from typing import Optional
from app.utils.vector_search import vector_search
from app.utils.openai_utils import query_router, get_mongo_pipeline, get_llm_response
from app.utils.format_utils import normalise_query
from pymongo.errors import OperationFailure
from app.db.upsert import insert_query_document
from app.db.conn import MongoDBConnection
from app.db.get import get_response_from_pipeline, get_thread_metadata_and_top_comments
from app.schemas.query_post_response import QueryPostResponse
from app.schemas.message import Message
from app.schemas.role import Role
from app.schemas.route import Route


def query_post(
    db_conn: MongoDBConnection,
    query: list[Message],
    username: str,
    chat_id: Optional[str] = None,
) -> QueryPostResponse:
    query = normalise_query(query)
    query_id = ObjectId()
    query_doc = {
        "_id": query_id,
        # if chat_id is none, this is the first question in the conversation
        # so we set the chat_id to the query_id of the first question
        "chat_id": ObjectId(chat_id) if chat_id else query_id,
        "updated_utc": int(time.time()),
        "query": query[-1].content,
    }
    original_user_query = deepcopy(query)

    is_error = False
    num_tries = 0
    MAX_TRIES = 3
    while num_tries < MAX_TRIES:
        try:
            all_similar_threads = []
            route = query_router(original_user_query)
            print(f"[INFO] Route: {route}")
            use_vector_search = route is Route.VECTOR
            if not use_vector_search:
                mongo_pipeline_obj = get_mongo_pipeline(original_user_query)
                query_doc.update(mongo_pipeline_obj)
                query[-1].content = (
                    f"""User Query:\n{query[-1].content}\n\nData from database:"""
                )

                print(
                    f"pipeline: {mongo_pipeline_obj.pipeline} reason: {mongo_pipeline_obj.reason}"
                )

                if mongo_pipeline_obj.pipeline:
                    mongodb_data = get_response_from_pipeline(
                        db_conn,
                        mongo_pipeline_obj.collection_name,
                        mongo_pipeline_obj.pipeline,
                    )
                    if len(mongodb_data) > 0:
                        _, similar_threads = get_thread_metadata_and_top_comments(
                            db_conn, mongodb_data
                        )
                        if len(similar_threads) > 0:
                            all_similar_threads.extend(similar_threads)
                        query[-1].content += f"""\n{mongodb_data}"""
                    else:
                        # if the data returned is empty, try doing a vector search
                        use_vector_search = True

            if use_vector_search:
                thread_collection = db_conn.get_collection("thread")

                vector_search_result = vector_search(
                    original_user_query, thread_collection
                )
                # only store the 'id' and 'vector_search_score' field into query_doc
                query_doc["vector_search_result"] = [
                    {"id": result["id"], "score": result["vector_search_score"]}
                    for result in vector_search_result
                ]
                search_result, similar_threads = get_thread_metadata_and_top_comments(
                    db_conn, vector_search_result
                )
                if len(similar_threads) > 0:
                    all_similar_threads.extend(similar_threads)

                query[-1].content += f"""\n{search_result}"""

            response = get_llm_response(query)
            if len(all_similar_threads) > 0:
                # remove duplicates and sort by score in descending order
                all_similar_threads = sorted(
                    set(all_similar_threads), key=lambda x: x[1], reverse=True
                )
                all_similar_threads_formatted = "**Relevant posts**\n"
                # el = a tuple of (formatted similar thread (str), score (int))
                for i, el in enumerate(all_similar_threads):
                    all_similar_threads_formatted += f"{i+1}. {el[0]}\n"
                response += f"\n\n{all_similar_threads_formatted}"
            query_with_response = query + [
                Message(role=Role.ASSISTANT, content=response)
            ]
            query_doc["response"] = response

            # when a new query is made, the user's vote is guaranteed to be 0
            return QueryPostResponse(
                response=query_with_response,
                query_id=query_doc["_id"],
                chat_id=query_doc["chat_id"],
                user_vote=0,
            )
        except Exception as e:
            num_tries += 1
            is_error = True
            query_doc["error"] = str(e)
            if isinstance(e, OperationFailure):
                query_doc["error_type"] = "operation_failure"
            else:
                query_doc["error_type"] = "others"
            if num_tries >= MAX_TRIES:
                raise e
        finally:
            # only upsert the query document if the number of tries is exhausted or no error occurred
            if num_tries >= MAX_TRIES or not is_error:
                query_doc["is_error"] = is_error
                insert_query_document(db_conn, query_doc, username)
