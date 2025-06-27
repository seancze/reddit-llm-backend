# reddit-llm-backend

## Description

This repository provides all backend endpoints for https://reddit-llm.vercel.app/. The frontend repository can be found [here](https://github.com/seancze/reddit-llm-frontend).

### Endpoints

#### `GET /health`

- Checks if the backend service is running

#### `POST /query`

- Generates a new LLM response to a user's query

An overview of how the RAG pipeline works is shown below:
![RAG pipeline](assets/rag-pipeline.png)

#### `PUT /vote`

- Updates an existing query document with a user's vote
- A thumbs up corresponds to a vote of 1
- A thumbs down corresponds to a vote of -1

#### `GET /chat/[id]`

- Retrieves an existing chat by id
- If the chat has been deleted or the id does not exist, a 404 error is returned

#### `GET /chat`

- Retrieves the first query of the most recent 25 chats that have not been deleted
- Accepts a 0-indexed `page` query parameter to retrieve older chats. For example, `GET /chat?page=1` retrieves the 26th to 50th chat, sorted in reverse chronological order

#### `DELETE /chat/[id]`

- Deletes a chat by setting `is_deleted=True`
- In order to investigate malicious requests, the chat is not actually deleted from the database

## Installation

1. Ensure that [Git LFS](https://git-lfs.com/) is installed locally
2. Install necessary dependencies by running `pip install -r requirements.txt`
3. Rename `.env-template` to `.env` and fill up the `.env` file. `JWT_SECRET` can be any value so long as it is the same as `AUTH_SECRET` in [the frontend repository](https://github.com/seancze/reddit-llm-frontend).

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

### Running on docker

**Build image**

```shell
docker build -t reddit-llm-backend app
```

**Run image**

```shell
docker run -p 8000:8000 --env-file .env reddit-llm-backend
```

### Deploy to Heroku

```shell
git subtree push --prefix app heroku main
```

- We can only deploy a subtree because Git LFS is not supported by Heroku

## Testing

To get started, set your `OPENAI_API_KEY` environment variable, or other required keys for the providers you selected.

### Run evaluation

**End-to-end**

```shell
npx promptfoo@latest eval -c test/end_to_end/promptfooconfig.yaml --no-cache
```

**Mongo pipeline**

```shell
npx promptfoo@latest eval -c test/query_router/promptfooconfig.yaml --no-cache
```

**View logs**

```shell
npx promptfoo@latest eval -c test/end_to_end/promptfooconfig.yaml --no-cache --verbose
```

### View evaluation UI

```shell
npx promptfoo@latest view
```

Click [here](https://www.promptfoo.dev/docs/getting-started/) for more information.
