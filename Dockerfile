FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY generate.py .
COPY wallapper.jpg .

ARG FLAG
ENV FLAG=${FLAG}

RUN python generate.py --flag "${FLAG}" --input wallapper.jpg --output /image.png
