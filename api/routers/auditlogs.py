from fastapi import APIRouter, Depends, HTTPException
from api.database import get_database
from api.models import AuditLogs
from .auth import get_current_user
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
)

db_dependency = Annotated[Session, Depends(get_database)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("", status_code=status.HTTP_200_OK)
async def get_logs(db: db_dependency, user: user_dependency):
    """
    ## Gets all Logs

    This endpoint allows you to list all the Logs.

    - **Permissions**:

        - To access this API Endpoint, the User must possess one of the following roles: `Admin` or `Contributor`.

    - **Request Body**:

        - `None`

    - **Response**:

        - `list[AuditLogs]`: A list containing all the Logs saved in the DataBase.
    """
    if user.get("role").casefold() == "reader":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"The user '{user.get("username")}' doesn't have permission to list all the Logs.",
        )

    all_logs = db.query(AuditLogs).all()

    return all_logs
