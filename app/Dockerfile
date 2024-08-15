FROM python:3.12.4-slim

WORKDIR /

# copy the directory contents at /app into the container at /app
COPY /app /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# the '-' argument after access-logfile and error-logfile tells Gunicorn to log to stdout/stderr
# this allows us to view our own Python print statements in the Docker logs
CMD gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --access-logfile - --error-logfile -