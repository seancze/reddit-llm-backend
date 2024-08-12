# reddit-llm-backend

## Installation
1. Install necessary dependencies by running `pip install -r requirements.txt`

## Usage

### Deploy locally using FastAPI
```shell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --workers 4
```
- This command enables auto-reloading, so the server will restart when you make changes to your code (useful for development)
- This command supports 4 concurrent workers
