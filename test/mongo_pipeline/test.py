import sys
import os

# Get the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory of the current directory
parent_dir = os.path.dirname(current_dir)
# Get the parent directory of the parent directory (which should contain 'app')
grandparent_dir = os.path.dirname(parent_dir)
# Add the grandparent directory to sys.path
sys.path.append(grandparent_dir)
from app.utils.openai_utils import get_mongo_pipeline
from app.db.conn import MongoDBConnection
from app.schemas.message import Message
from app.schemas.role import Role


def call_api(prompt, options, context):
    enable_test = context["vars"]["enable_test"]
    if enable_test.upper() == "FALSE":
        return {
            "output": {
                "pipeline": None,
                "reason": "Test case is disabled. Set 'enable_test' to 'True' to enable it.",
            },
        }
    try:
        db_conn = MongoDBConnection()
        user_query = context["vars"]["query"]
        messages = [Message(content=user_query, role=Role.USER)]

        pipeline_obj = get_mongo_pipeline(messages)
        pipeline = pipeline_obj.pipeline

        result = {
            "output": {
                "pipeline": pipeline,
                "reason": pipeline_obj.reason,
            }
        }

        return result
    except Exception as e:
        raise e
    finally:
        db_conn.close()
