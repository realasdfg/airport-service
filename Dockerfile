FROM python:3.13.14-slim
LABEL maintainer="realasdfga@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

RUN adduser --disabled-password --no-create-home user

USER user
