from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from api.database import SessionLocal
from api.models import Users
from typing import Annotated
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from starlette import status
import jwt

router = APIRouter(
    prefix="/authentication",
    tags=["authentication"],
)

SECRET_KEY = "4de9ea34a3ef5306415f8e5289c2d8998343fb13261944f340e702f02df2bea1"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="authentication/token")


class Token(BaseModel):
    access_token: str
    token_type: str


def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_database)]
token_dependency = Annotated[str, Depends(oauth2_bearer)]
login_form_data = Annotated[OAuth2PasswordRequestForm, Depends()]


def authenticate_user(username: str, password: str, db: db_dependency):
    user = db.query(Users).filter(Users.username == username).first()

    # If User is not found or Password doesn't match, return False
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        return False

    return user


def create_access_token(
    username: str, user_id: int, role: str, expires_delta: timedelta
):
    encode = {
        "sub": username,
        "id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc).replace(tzinfo=None) + expires_delta,
    }

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: token_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access."
        )
    else:
        username = payload.get("sub")
        user_id = payload.get("id")
        role = payload.get("role")

        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access."
            )
        return {"username": username, "id": user_id, "role": role}


@router.post("/token", response_model=Token)
async def get_access_token(
    login_form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    """
    ## Create a Bearer Token

    This endpoint allows you to authenticate and get a Bearer Token.

    - **Permissions**:

        - To access this API Endpoint, the User must possess one of the following roles: `Admin`, `Contributor` or `Reader`.

    - **Request Body**:

        - `username`: The Username that will authenticate.

        - `password`: The User's Password.

    - **Response**:

        - `list[AuditLogs]`: A list containing all the Logs saved in the DataBase.
    """
    user = authenticate_user(
        username=login_form_data.username, password=login_form_data.password, db=db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access."
        )

    token = create_access_token(
        username=user.username,
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=30),
    )

    return {"access_token": token, "token_type": "Bearer"}
