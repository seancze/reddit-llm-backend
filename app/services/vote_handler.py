from app.db.upsert import update_query_vote
from app.db.conn import MongoDBConnection


def handle_vote(db_conn: MongoDBConnection, query_id: str, vote: int, username: str):
    result = update_query_vote(db_conn, query_id, vote, username)
    if result:
        if result.matched_count > 0:
            if result.modified_count > 0:
                print("Document updated successfully")
            else:
                print("Document found but no changes were made")
        else:
            print("Error: No document found with the given ID")
    else:
        print("Error: Operation failed due to invalid ObjectId")
