FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm

COPY . /app

RUN useradd -m fastapi-user && \
    chown -R fastapi-user:fastapi-user /app && \
    chown -R fastapi-user:fastapi-user /root/.cache

USER fastapi-user

EXPOSE 8000

# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "-b", "0.0.0.0:8000", "-w", "2"]