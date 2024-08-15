import uvicorn
import os
from fastapi import FastAPI
from app.db.conn import lifespan
from app.api.routes import router

app = FastAPI(lifespan=lifespan)
app.include_router(router)

# heroku may set the port dynamically
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=port)
