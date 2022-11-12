# syntax=docker/dockerfile:1

FROM python:3.11-alpine

RUN apk add build-base libffi-dev
RUN python -m venv /venv
COPY requirements.txt .
RUN . /venv/bin/activate && pip install -r requirements.txt

FROM python:3.11-alpine

RUN apk add libffi
RUN adduser -D app

COPY --from=0 /venv /venv/
WORKDIR /app
COPY passencrypt.py .
COPY spamsubmit.py .

WORKDIR /config

USER app

CMD . /venv/bin/activate && exec python spamsubmit.py spamsubmit.conf
