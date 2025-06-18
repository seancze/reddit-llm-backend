import traceback
from fastapi import APIRouter, HTTPException, Depends, Path, Body
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from app.schemas.query_request import QueryRequest
from app.schemas.query_get_response import QueryGetResponse
from app.schemas.query_post_response import QueryPostResponse
from app.schemas.vote_request import VoteRequest
from app.schemas.chat_list_response import ChatListResponse
from app.services.query.post import query_post
from app.services.chat.get import chat_get
from app.services.vote.put import vote_put
from app.services.chat.list import chat_list
from app.services.chat.delete import chat_delete
from app.db.conn import get_db_client
from app.utils.auth_utils import verify_token, verify_token_or_anonymous
from typing import Optional, List


router = APIRouter()


@router.get("/health")
async def root(username: str = Depends(verify_token)):
    return {"message": "Healthy", "user": username}


@router.post("/query", response_model=QueryPostResponse)
async def api_post_user_query(
    query: QueryRequest,
    db_conn=Depends(get_db_client),
    username: str = Depends(verify_token),
):
    try:
        response = await run_in_threadpool(
            query_post, db_conn, query.query, username, query.chat_id
        )
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


@router.get("/chat/{chat_id}", response_model=QueryGetResponse)
async def api_get_chat(
    db_conn=Depends(get_db_client),
    username: Optional[str] = Depends(verify_token_or_anonymous),
    chat_id: str = Path(description="The ID of the chat"),
):
    try:
        response = await run_in_threadpool(chat_get, db_conn, chat_id, username)
        return response
    except HTTPException as e:
        raise e
    except:
        print(traceback.format_exc())
        raise HTTPException(status_code=500)


@router.get("/chat", response_model=List[ChatListResponse])
async def api_list_chat(
    db_conn=Depends(get_db_client),
    username: str = Depends(verify_token),
):
    try:
        response = await run_in_threadpool(chat_list, db_conn, username)
        return response
    except HTTPException as e:
        raise e
    except:
        print(traceback.format_exc())
        raise HTTPException(status_code=500)


@router.delete("/chat")
async def api_delete_chat(
    db_conn=Depends(get_db_client),
    username: str = Depends(verify_token),
    chat_id: str = Body(..., embed=True, description="The ID of the chat"),
):
    try:
        deleted_queries_count = await run_in_threadpool(chat_delete, db_conn, chat_id)
        return JSONResponse(
            status_code=200,
            content={
                "message": f"{username} deleted {deleted_queries_count} queries for chat: {chat_id}"
            },
        )
    except HTTPException as e:
        raise e
    except:
        print(traceback.format_exc())
        raise HTTPException(status_code=500)
