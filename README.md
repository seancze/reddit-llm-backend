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

### Use gunicorn for deployment in production environments
```shell
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
- See [here](https://www.uvicorn.org/#running-with-gunicorn) for more information

