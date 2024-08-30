import sys
import os

# add parent path to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.query_handler import handle_user_query
from app.db.conn import MongoDBConnection
from app.utils.openai_utils import get_mongo_pipeline

try:
    user_query = "What are the key challenges that youths face?"
    db_conn = MongoDBConnection()
    # pipeline = get_mongo_pipeline(user_query)
    # print(f"pipeline: {pipeline}")
    response = handle_user_query(db_conn, user_query, "PLACEHOLDER")
    print(f"response: {response} type: {type(response)}")
except Exception as e:
    raise e
finally:
    db_conn.close()
