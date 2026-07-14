FROM python:3.13.14-slim
LABEL maintainer="realasdfga@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /files/media \
    && adduser --disabled-password --no-create-home user \
    && chown -R user /files/media \
    && chmod -R 755 /files/media

USER user
