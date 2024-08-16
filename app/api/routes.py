import traceback
from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from app.schemas.query_request import QueryRequest
from app.schemas.query_response import QueryResponse
from app.schemas.vote_request import VoteRequest
from app.services.query_handler import handle_user_query
from app.services.vote_handler import handle_vote
from app.db.conn import get_db_client


router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def api_handle_user_query(query: QueryRequest, db_conn=Depends(get_db_client)):
    try:
        response = await run_in_threadpool(handle_user_query, query.query, db_conn)
        return response
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put("/vote")
async def api_handle_vote(vote_request: VoteRequest, db_conn=Depends(get_db_client)):
    try:
        await run_in_threadpool(
            handle_vote, vote_request.query_id, vote_request.vote, db_conn
        )
        return JSONResponse(
            status_code=200,
            content={"message": f"Successfully updated vote to {vote_request.vote}"},
        )
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")
