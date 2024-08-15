import sys
import os

# add parent path to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.query_handler import handle_user_query
from app.db.conn import MongoDBConnection


try:
    user_query = "What are the key challenges that youths face?"
    db_conn = MongoDBConnection()
    response = handle_user_query(user_query, db_conn)
except Exception as e:
    raise e
finally:
    db_conn.close()


print(f"response: {response}")
