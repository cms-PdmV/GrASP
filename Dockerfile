# Build web application bundle
FROM node:16-buster-slim@sha256:1417528032837e47462ea8cfe983108b0152f989e95cba2ddfbe0f0ddc2dcfbd AS frontend

WORKDIR /usr/app

COPY frontend .

RUN npm install
RUN npm run build

# Build dependencies
FROM python:3.11.7-alpine3.19@sha256:6aa46819a8ff43850e52f5ac59545b50c6d37ebd3430080421582af362afec97 AS build
RUN apk update && apk upgrade
RUN pip install --upgrade pip setuptools wheel

WORKDIR /usr/app
RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# Create image for deployment
FROM python:3.11.7-alpine3.19@sha256:6aa46819a8ff43850e52f5ac59545b50c6d37ebd3430080421582af362afec97 AS backend
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
