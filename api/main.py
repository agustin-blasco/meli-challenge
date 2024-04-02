from fastapi import FastAPI, Response, Request, Depends, HTTPException
from api.routers import admin, auth, auditlogs, tornodes
from api.database import engine, get_database, SessionLocal
from api.routers.auth import get_current_user
from api import models
from typing import Annotated
from sqlalchemy.orm import Session

app = FastAPI(swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})

models.Base.metadata.create_all(bind=engine)
db_dependency = Annotated[Session, Depends(get_database)]


app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(tornodes.router)
app.include_router(auditlogs.router)


@app.middleware("http")
async def api_logging(request: Request, call_next):
    response = await call_next(request)

    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    await push_audit_log(request=request, response=response, db=SessionLocal())

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )


async def push_audit_log(request: Request, response: Response, db: db_dependency):
    
    # This list will hold the Website Endpoints that don't require to be logged in the DB.
    excluded_endpoints = [
        "/docs",
        "/favicon.ico",
        "/openapi.json"
    ]

    if request.url.path in excluded_endpoints:
        return

    try:
        username = await get_current_user(
            request.headers.get("Authorization").split(" ")[-1]
        )
    except (HTTPException, AttributeError):
        username = {"username": "anonymous"}

    log_model = models.AuditLogs(
        username=username.get("username"),
        method=request.method,
        endpoint=request.url.path,
        host=request.url.hostname,
        status_code=response.status_code,
    )

    # return log_model
    db.add(log_model)
    db.commit()
