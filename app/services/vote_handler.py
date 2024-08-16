from app.db.upsert import update_query_vote
from app.db.conn import MongoDBConnection


def handle_vote(query_id: str, vote: int, db_conn: MongoDBConnection):
    result = update_query_vote(query_id, vote, db_conn)
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
