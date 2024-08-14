import os
import traceback
from pymongo import MongoClient
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


class MongoDBConnection:
    def __init__(self):
        uri = os.environ.get("MONGODB_URI")
        self.client = MongoClient(uri)
        self.db = self.client["reddit_db"]

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def close(self):
        self.client.close()


@contextmanager
def mongodb_connection():
    connection = MongoDBConnection()
    try:
        yield connection
    except Exception as e:
        print(traceback.format_exc())
        print(f"IMPORTANT: Please ensure that your VPN is disabled")
        raise e
    finally:
        connection.close()
