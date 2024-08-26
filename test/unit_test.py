import sys
import os

# add parent path to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.query_handler import handle_user_query
from app.utils.openai_utils import get_mongo_pipeline
from app.db.conn import MongoDBConnection


def call_api(prompt, options, context):
    try:
        db_conn = MongoDBConnection()
        enable_test = context["vars"]["enable_test"]
        is_pipeline_generated = context["vars"]["is_pipeline_generated"]
        if enable_test.upper() == "FALSE":
            return {
                "output": {
                    "response": "Test case is disabled. Set 'enable_test' to 'True' to enable it.",
                    "pipeline": [] if is_pipeline_generated.upper() == "TRUE" else None,
                },
            }
        user_query = context["vars"]["query"]

        response = handle_user_query(user_query, db_conn)
        pipeline_obj = get_mongo_pipeline(user_query)
        pipeline = pipeline_obj["pipeline"]
        result = {"output": {"response": response.response, "pipeline": pipeline}}

        return result
    except Exception as e:
        raise e
    finally:
        db_conn.close()
