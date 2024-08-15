import uvicorn
from fastapi import FastAPI
from app.db.conn import lifespan
from app.api.routes import router

app = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
