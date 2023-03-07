# Build web application bundle
FROM node:16-buster-slim@sha256:1417528032837e47462ea8cfe983108b0152f989e95cba2ddfbe0f0ddc2dcfbd AS frontend

WORKDIR /usr/app

COPY frontend .

RUN npm install
RUN npm run build

# Build dependencies
FROM python:3.11.2-slim-buster@sha256:8f827e9cc31e70c5bdbed516d7d6627b10afad9b837395ac19315685d13b40c2 AS build

WORKDIR /usr/app
RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# Create image for deployment
FROM python:3.11.2-slim-buster@sha256:8f827e9cc31e70c5bdbed516d7d6627b10afad9b837395ac19315685d13b40c2 AS backend

RUN groupadd -g 999 python && useradd -r -u 999 -g python python

RUN mkdir /usr/app && chown python:python /usr/app
WORKDIR /usr/app

COPY --chown=python:python . .
RUN rm -rf frontend/*

COPY --chown=python:python --from=frontend /usr/app/dist ./frontend/dist
COPY --chown=python:python --from=build /usr/app/venv ./venv

USER 999

ENV PATH="/usr/app/venv/bin:$PATH"
CMD [ "gunicorn", "main:app" ]