import time
from bson import ObjectId
from typing import Optional
from app.utils.vector_search import vector_search
from app.utils.openai_utils import get_mongo_pipeline, get_llm_response
from app.utils.format_utils import normalise_query, format_vector_search_result
from pymongo.errors import OperationFailure
from app.db.upsert import insert_query_document
from app.db.conn import MongoDBConnection
from app.db.get import get_response_from_pipeline
from app.schemas.query_post_response import QueryPostResponse
from app.schemas.message import Message
from app.schemas.role import Role


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

    is_error = False
    num_tries = 0
    MAX_TRIES = 3
    while num_tries < MAX_TRIES:
        try:
            mongo_pipeline_obj = get_mongo_pipeline(query)
            query_doc.update(mongo_pipeline_obj)

            # if the pipeline is None, it means that we are not supposed to query the database
            # hence, we set vector search to True
            use_vector_search = mongo_pipeline_obj.pipeline is None
            query[-1].content = (
                f"""User Query:\n{query[-1].content}\n\nData from database:"""
            )

            if mongo_pipeline_obj.pipeline:
                mongodb_data = get_response_from_pipeline(
                    db_conn,
                    mongo_pipeline_obj.collection_name,
                    mongo_pipeline_obj.pipeline,
                )
                # if the data returned is empty we should use vector search
                if len(mongodb_data) == 0:
                    use_vector_search = True
                else:
                    query[
                        -1
                    ].content += f"""\n{mongodb_data}\nDatabase query: {mongo_pipeline_obj.pipeline}"""

            if use_vector_search:
                thread_collection = db_conn.get_collection("thread")

                vector_search_result = vector_search(query, thread_collection)
                # only store the 'id' and 'vector_search_score' field into query_doc
                query_doc["vector_search_result"] = [
                    {"id": result["id"], "score": result["vector_search_score"]}
                    for result in vector_search_result
                ]
                search_result = format_vector_search_result(
                    db_conn, vector_search_result
                )

                query[-1].content += f"""\n{search_result}"""

            response = get_llm_response(query)
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
