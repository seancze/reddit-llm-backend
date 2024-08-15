import traceback
from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from app.schemas.query import Query
from app.schemas.response import Response
from app.services.query_handler import handle_user_query
from app.db.conn import get_db_client


router = APIRouter()


@router.post("/query", response_model=Response)
async def api_handle_user_query(query: Query, db_conn=Depends(get_db_client)):
    try:
        response = await run_in_threadpool(handle_user_query, query.query, db_conn)
        return Response(response=response)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")
