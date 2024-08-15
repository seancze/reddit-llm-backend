import openai
import time
import os
from dotenv import load_dotenv
from app import constants
from app.utils.vector_search import vector_search
from app.utils.mongodb_query import get_mongo_pipeline, query_mongodb
from app.utils.format_utils import normalise_query
from pymongo.errors import OperationFailure
from app.db.upsert import upsert_query_document
from app.db.conn import MongoDBConnection
from app.db.get import get_cached_response

load_dotenv()


def handle_user_query(query: str, db_conn: MongoDBConnection):
    query = normalise_query(query)
    query_doc = {"updated_utc": int(time.time()), "query": query, "query_count": 1}
    is_error = False
    try:
        # check if the query has been made recently
        cached_doc = get_cached_response(query, db_conn)
        if cached_doc:
            query_doc["used_cache"] = True
            query_doc.update(cached_doc)
            is_error = cached_doc.get("is_error", False)
            if is_error:
                raise Exception("Cached document returned an error previously")
            return cached_doc["response"]

        mongo_pipeline_obj = get_mongo_pipeline(query)
        query_doc.update(mongo_pipeline_obj)

        # if the pipeline is None, it means that we are not supposed to query the database
        # hence, we set vector search to True
        use_vector_search = mongo_pipeline_obj["pipeline"] is None
        prompt = f"""User Query:
    {query}

    Data from database:"""

        if mongo_pipeline_obj["pipeline"]:
            mongodb_data = query_mongodb(
                mongo_pipeline_obj["collection_name"],
                mongo_pipeline_obj["pipeline"],
                db_conn,
            )
            # if the data returned is empty we should use vector search
            if len(mongodb_data) == 0:
                use_vector_search = True
            else:
                prompt += f"""\n{mongodb_data}\nDatabase query: {mongo_pipeline_obj["pipeline"]}"""
        if use_vector_search:
            thread_collection = db_conn.get_collection("thread")
            comment_collection = db_conn.get_collection("comment")

            vector_search_result = vector_search(query, thread_collection)
            # only store the 'id' and 'vector_search_score' field into query_doc
            query_doc["vector_search_result"] = [
                {"id": result["id"], "score": result["vector_search_score"]}
                for result in vector_search_result
            ]

            search_result = ""

            for i, result in enumerate(vector_search_result):
                thread_id = result.get("id")
                # for each thread_id, get the top 5 comments from the 'comment' collection based on the score and add them to the search result
                comments = (
                    comment_collection.find(
                        {
                            "parent_id": f"t3_{thread_id}"  # we use parent_id to ensure that we only get top-level comments
                        },
                        {"_id": 0, "score": 1, "body": 1},
                    )
                    .sort([("score", -1)])
                    .limit(3)
                )

                # ensure that the comments are formatted like this: "Comment (Score: {score}): {body} \n"
                comments_str = " \n".join(
                    [
                        f"Comment (Score: {comment.get('score', 'N/A')}): {comment.get('body', 'N/A')}"
                        for comment in comments
                    ]
                )

                search_result += f"""Thread {i+1} (Score: {result.get('score', 'N/A')})\nTitle: {result.get('title', 'N/A')}\nURL: https://reddit.com{result.get('permalink', 'N/A')}\nBody: {result.get('selftext', "N/A")}\n{comments_str}\n\n\n"""
                # print(f"search_result: {search_result}")

            prompt += f"""\n{search_result}"""

        completion = openai.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL"),
            messages=[
                {"role": "system", "content": constants.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        response = completion.choices[0].message.content
        query_doc["response"] = response

        return response
    except Exception as e:
        is_error = True
        query_doc["error"] = str(e)
        if isinstance(e, OperationFailure):
            query_doc["error_type"] = "operation_failure"
        else:
            query_doc["error_type"] = "others"
        raise e
    finally:
        query_doc["is_error"] = is_error
        upsert_query_document(query_doc, db_conn)
