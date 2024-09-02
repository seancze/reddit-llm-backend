import traceback
from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from app.schemas.query_request import QueryRequest
from app.schemas.query_response import QueryResponse
from app.schemas.vote_request import VoteRequest
from app.services.query.post import query_post
from app.services.vote.put import vote_put
from app.db.conn import get_db_client
from app.utils.auth_utils import verify_token


router = APIRouter()


@router.get("/health")
async def root(username: str = Depends(verify_token)):
    return {"message": "Healthy", "user": username}


@router.post("/query", response_model=QueryResponse)
async def api_post_user_query(
    query: QueryRequest,
    db_conn=Depends(get_db_client),
    username: str = Depends(verify_token),
):
    try:
        response = await run_in_threadpool(query_post, db_conn, query.query, username)
        return response
    except:
        print(traceback.format_exc())
        raise HTTPException(status_code=500)


@router.put("/vote")
async def api_put_vote(
    vote_request: VoteRequest,
    db_conn=Depends(get_db_client),
    username: str = Depends(verify_token),
):
    try:
        await run_in_threadpool(
            vote_put,
            db_conn,
            vote_request.query_id,
            vote_request.vote,
            username,
        )
        return JSONResponse(
            status_code=200,
            content={"message": f"Successfully updated vote to {vote_request.vote}"},
        )
    except:
        print(traceback.format_exc())
        raise HTTPException(status_code=500)
