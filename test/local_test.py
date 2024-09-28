import sys
import os

# add parent path to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.query.post import query_post
from app.db.conn import MongoDBConnection
from app.utils.openai_utils import get_mongo_pipeline
from app.schemas.message import Message
from app.schemas.role import Role
from app.db.get import get_response_from_pipeline

try:
    user_query = "What are the key challenges that youths face?"
    user_query = "What are the top 5 posts since 1st September 2024?\nCurrent time in seconds since epoch: 1726302088"
    user_query = "What is the average number of comments on a thread?"
    message = [Message(content=user_query, role=Role.USER)]
    db_conn = MongoDBConnection()
    pipeline = get_mongo_pipeline(message)
    print(f"pipeline: {pipeline}")
    response = get_response_from_pipeline(db_conn, "thread", pipeline.pipeline)
    # response = query_post(db_conn, message, "PLACEHOLDER", "66efd4752fed95286650b9a3")
    print(f"response: {response} type: {type(response)}")
except Exception as e:
    raise e
finally:
    db_conn.close()

# {"$project": {"selftext_embedding": 0, "_id": 0}}
