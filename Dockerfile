# Build web application bundle
FROM node:16-buster-slim@sha256:1417528032837e47462ea8cfe983108b0152f989e95cba2ddfbe0f0ddc2dcfbd AS frontend

WORKDIR /usr/app

COPY frontend .

RUN npm install
RUN npm run build

# Build dependencies
FROM python:3.11.10-alpine3.20@sha256:f089154eb2546de825151b9340a60d39e2ba986ab17aaffca14301b0b961a11c AS build
RUN apk add git
RUN apk update && apk upgrade
RUN pip install --upgrade pip setuptools wheel

WORKDIR /usr/app
RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# Create image for deployment
FROM python:3.11.10-alpine3.20@sha256:f089154eb2546de825151b9340a60d39e2ba986ab17aaffca14301b0b961a11c AS backend
RUN apk update && apk upgrade
RUN pip install --upgrade pip setuptools wheel

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
