# Build web application bundle
FROM node:16-buster-slim@sha256:1417528032837e47462ea8cfe983108b0152f989e95cba2ddfbe0f0ddc2dcfbd AS frontend

WORKDIR /usr/app

COPY frontend .

RUN npm install
RUN npm run build

# Build dependencies
FROM python:3.11.3-alpine3.18@sha256:caafba876f841774905f73df0fcaf7fe3f55aaf9cb48a9e369a41077f860d4a7 AS build

WORKDIR /usr/app
RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# Create image for deployment
FROM python:3.11.3-alpine3.18@sha256:caafba876f841774905f73df0fcaf7fe3f55aaf9cb48a9e369a41077f860d4a7 AS backend

RUN addgroup -g 1001 pdmv && adduser --disabled-password -u 1001 -G pdmv pdmv

RUN mkdir /usr/app && chown pdmv:pdmv /usr/app
WORKDIR /usr/app

COPY --chown=pdmv:pdmv . .
RUN rm -rf frontend/*

COPY --chown=pdmv:pdmv --from=frontend /usr/app/dist ./frontend/dist
COPY --chown=pdmv:pdmv --from=build /usr/app/venv ./venv

USER 1001

ENV PATH="/usr/app/venv/bin:$PATH"
CMD [ "gunicorn", "main:app" ]
