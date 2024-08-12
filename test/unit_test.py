import sys
import os

# add parent path to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.query_handler import handle_user_query


def call_api(prompt, options, context):
    enable_test = context["vars"]["enable_test"]
    if enable_test.upper() == "FALSE":
        return {
            "output": "Test case is disabled. Set 'enable_test' to 'True' to enable it.",
        }
    user_query = context["vars"]["query"]
    response, pipeline = handle_user_query(user_query)
    result = {
        "output": {"response": response, "pipeline": pipeline},
    }

    return result
