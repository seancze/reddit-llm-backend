import time
from bson import ObjectId
from app.utils.vector_search import vector_search
from app.utils.openai_utils import get_mongo_pipeline, get_llm_response
from app.utils.format_utils import normalise_query, format_vector_search_result
from pymongo.errors import OperationFailure
from app.db.upsert import upsert_query_document
from app.db.conn import MongoDBConnection
from app.db.get import get_cached_response, get_response_from_pipeline
from app.schemas.query_response import QueryResponse


def handle_user_query(query: str, db_conn: MongoDBConnection):
    query = normalise_query(query)
    query_doc = {
        "_id": ObjectId(),
        "updated_utc": int(time.time()),
        "query": query,
        "query_count": 1,
    }
    is_error = False
    try:
        # check if the query has been made recently
        cached_doc = get_cached_response(query, db_conn)
        if cached_doc:
            query_doc["used_cache"] = True
            # amongst other fields, this updates "_id" to the id of the cached_doc
            query_doc.update(cached_doc)
            is_error = cached_doc.get("is_error", False)
            if is_error:
                raise Exception("Cached document returned an error previously")
            return QueryResponse(
                response=cached_doc["response"], query_id=cached_doc["_id"]
            )

        mongo_pipeline_obj = get_mongo_pipeline(query)
        query_doc.update(mongo_pipeline_obj)

        # if the pipeline is None, it means that we are not supposed to query the database
        # hence, we set vector search to True
        use_vector_search = mongo_pipeline_obj["pipeline"] is None
        prompt = f"""User Query:
    {query}

    Data from database:"""

        if mongo_pipeline_obj["pipeline"]:
            mongodb_data = get_response_from_pipeline(
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

            vector_search_result = vector_search(query, thread_collection)
            # only store the 'id' and 'vector_search_score' field into query_doc
            query_doc["vector_search_result"] = [
                {"id": result["id"], "score": result["vector_search_score"]}
                for result in vector_search_result
            ]
            search_result = format_vector_search_result(vector_search_result, db_conn)

            prompt += f"""\n{search_result}"""

        response = get_llm_response(prompt)
        query_doc["response"] = response

        return QueryResponse(response=response, query_id=query_doc["_id"])
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
