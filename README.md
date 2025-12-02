# Reddit LLM (Backend)

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

## Deploy locally

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

### Deploy locally on Docker

**Build image**

```shell
docker build -t reddit-llm-backend app
```

**Run image**

```shell
docker run -d -p 8000:8000 --env-file .env reddit-llm-backend
```

- `-d` = Detaches the container from the terminal so it keeps running in the background

**Common Docker commands**

```shell
docker logs CONTAINER_ID -f
```

- `-f` = Stream logs continuously

## Deploy on AWS EC2

This repository uses GitHub Actions for automated deployment. On every push to `main`, the workflow automatically:

1. Checks out the latest code
2. Authenticates to EC2 using the private key
3. Pulls the latest changes on the EC2 instance
4. Builds a new Docker image
5. Stops the old container and starts a new one
6. Cleans up old Docker images

### Setting up your AWS EC2 instance

1. Follow the AWS guide [here](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/create-key-pairs.html#having-ec2-create-your-key-pair) to create a valid key pair
   - Remember to set permissions of your generated key: `chmod 400 key-pair-name.pem`
2. Connect to instance: `ssh -i "~/.ssh/key-pair-name.pem" EC2_USER@EC2_HOST`
3. Use root user: `sudo -s` (source: https://stackoverflow.com/questions/7407333/amazon-ec2-root-login)
4. Download pip3: `python3 -m ensurepip --upgrade` ([source](https://pip.pypa.io/en/stable/installation/))
   - `python3` should be pre-installed
5. Download git: `sudo dnf install git-all` ([source](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git))
6. Download Docker (applies to Amazon Linux 2023 images only)

```shell
# Install Docker from the Amazon Linux 2023 repos
sudo yum install -y docker

# Start Docker and enable it on boot
sudo systemctl start docker
sudo systemctl enable docker

# Allow ec2-user to run docker without sudo
sudo usermod -aG docker ec2-user
```

7. Clone this repository and navigate into the repository

```shell
cd ~
git clone https://github.com/seancze/reddit-llm-backend.git
cd reddit-llm-backend
```

8. Copy the `.env-template` into a `.env` file and update the values accordingly

## [Deprecated] Deploy to Heroku

```shell
git subtree push --prefix app heroku main
```

- We can only deploy a subtree because Git LFS is not supported by Heroku

### Force push using Git subtree

**Step 1: Create or update a split branch from the app folder**

```shell
git subtree split --prefix app -b heroku-deploy
```

**Step 2: Force push that split branch to the remote heroku on branch main**

```shell
git push heroku heroku-deploy:main --force
```

**Step 3: Delete the temporary split branch to keep your local branches clean**

```shell
git branch -D heroku-deploy
```

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
