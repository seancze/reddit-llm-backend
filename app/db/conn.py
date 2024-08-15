import os
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager

load_dotenv()


class MongoDBConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
            uri = os.environ.get("MONGODB_URI")
            cls._instance.client = MongoClient(uri, maxPoolSize=10, minPoolSize=5)
            cls._instance.db = cls._instance.client["reddit_db"]
            print(f"MongoDB connection created.")
        return cls._instance

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def get_active_connections(self):
        try:
            server_status = self.db.command("serverStatus")
            connections = server_status["connections"]
            return {
                "current": connections["current"],
                "available": connections["available"],
                "total_created": connections["totalCreated"],
            }
        except Exception as e:
            print(f"Error getting connection info: {e}")
            return None

    def print_connection_info(self):
        conn_info = self.get_active_connections()
        if conn_info:
            print(f"Current active connections: {conn_info['current']}")
            print(f"Available connections: {conn_info['available']}")
            print(f"Total connections created: {conn_info['total_created']}")
        else:
            print("Unable to retrieve connection information.")

    def close(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")


db_conn = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create a database client when the app starts
    global db_conn
    db_conn = MongoDBConnection()
    db_conn.print_connection_info()
    yield
    # close the database client when the app stops
    db_conn.close()


# used to ensure that we are able to get the (same) database instance after the app has started
def get_db_client():
    return db_conn
