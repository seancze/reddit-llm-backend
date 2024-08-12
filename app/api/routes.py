from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from app.schemas.query import Query
from app.schemas.response import Response
from app.services.query_handler import handle_user_query

router = APIRouter()


@router.post("/query", response_model=Response)
async def api_handle_user_query(query: Query):
    try:
        response, data = await run_in_threadpool(handle_user_query, query.query)
        return Response(response=response, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
