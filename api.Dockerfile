# temp stage
FROM python:3.12.2-alpine3.19 as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk add --update && \
    apk add build-base

COPY /api/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# final stage
FROM python:3.12.2-alpine3.19

WORKDIR /app

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN mkdir -p /var/lib/postgresql/data/

RUN pip install --no-cache /wheels/*
RUN pip uninstall -y pip==24.0