import time
from copy import deepcopy
from bson import ObjectId
from typing import Optional
from fastapi.concurrency import run_in_threadpool
from app.utils.vector_search import vector_search
from app.utils.openai_utils import query_router, get_llm_response
from app.utils.format_utils import normalise_query
from pymongo.errors import OperationFailure
from app.db.upsert import insert_query_document
from app.db.conn import MongoDBConnection
from app.db.get import get_response_from_pipeline, get_thread_metadata_and_top_comments
from app.schemas.query_post_response import QueryPostResponse
from app.schemas.message import Message
from app.schemas.role import Role
from app.schemas.route import Route
from app.services.query.mcp import query_mcp


async def query_post(
    db_conn: MongoDBConnection,
    query: list[Message],
    username: str,
    chat_id: Optional[str] = None,
) -> QueryPostResponse:
    start_time = time.time()
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

            # Time the routing decision
            route_start = time.time()
            route = await query_router(original_user_query)
            route_time = time.time() - route_start
            print(f"[PERF] Route decision took {route_time:.2f}s - Route: {route}")

            use_vector_search = route is Route.VECTOR
            if not use_vector_search:
                # Use MCP to query MongoDB
                mcp_start = time.time()
                mcp_result = await query_mcp(original_user_query)
                mcp_time = time.time() - mcp_start
                print(f"[PERF] MCP query took {mcp_time:.2f}s")

                # Extract pipeline information for query_doc
                if mcp_result.get("collection_name"):
                    query_doc["collection_name"] = mcp_result["collection_name"]
                if mcp_result.get("pipeline"):
                    query_doc["pipeline"] = mcp_result["pipeline"]
                if mcp_result.get("reason"):
                    query_doc["reason"] = mcp_result["reason"]

                # Update query content for LLM
                query[-1].content = (
                    f"""User Query:\n{query[-1].content}\n\nData from database:"""
                )

                print(
                    f"pipeline: {mcp_result.get('pipeline')} reason: {mcp_result.get('reason')}"
                )

                # If MCP returned a pipeline, execute it to get similar threads
                if mcp_result.get("pipeline") and mcp_result.get("collection_name"):
                    mongodb_data = await run_in_threadpool(
                        get_response_from_pipeline,
                        db_conn,
                        mcp_result["collection_name"],
                        mcp_result["pipeline"],
                    )
                    if len(mongodb_data) > 0:
                        _, similar_threads = await run_in_threadpool(
                            get_thread_metadata_and_top_comments, db_conn, mongodb_data
                        )
                        if len(similar_threads) > 0:
                            all_similar_threads.extend(similar_threads)
                        query[-1].content += f"""\n{mongodb_data}"""

                # Use the MCP response as the LLM response
                response = mcp_result.get("response", "No response generated")
            else:
                vector_start = time.time()
                thread_collection = db_conn.get_collection("thread")

                vector_search_result = await run_in_threadpool(
                    vector_search, original_user_query, thread_collection
                )
                vector_time = time.time() - vector_start
                print(f"[PERF] Vector search took {vector_time:.2f}s")
                # only store the 'id' and 'vector_search_score' field into query_doc
                query_doc["vector_search_result"] = [
                    {"id": result["id"], "score": result["vector_search_score"]}
                    for result in vector_search_result
                ]
                search_result, similar_threads = await run_in_threadpool(
                    get_thread_metadata_and_top_comments, db_conn, vector_search_result
                )
                if len(similar_threads) > 0:
                    all_similar_threads.extend(similar_threads)

                query[-1].content += f"""\n{search_result}"""

                # For vector search, use traditional LLM response
                llm_start = time.time()
                response = await run_in_threadpool(get_llm_response, query)
                llm_time = time.time() - llm_start
                print(f"[PERF] LLM response generation took {llm_time:.2f}s")

            # Add similar threads to response if available
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

            total_time = time.time() - start_time
            print(f"[PERF] Total query_post execution time: {total_time:.2f}s")

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
                await run_in_threadpool(
                    insert_query_document, db_conn, query_doc, username
                )
