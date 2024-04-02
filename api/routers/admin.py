from fastapi import APIRouter, Depends, HTTPException, Path
from passlib.context import CryptContext
from api.database import get_database
from api.models import Users
from api.routers.schemas import (
    Message,
    CreateUserRequest,
    UserUpdateRequest,
    CreateSuperAdminRequest,
)
from .auth import get_current_user
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

db_dependency = Annotated[Session, Depends(get_database)]
user_dependency = Annotated[dict, Depends(get_current_user)]

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
)
async def get_users(db: db_dependency, user: user_dependency):
    """
    ## Gets all Users

    This endpoint allows you to list all the Users, if ran by an Admin. Contributor and Reader roles will only return it's own user profile.

    - **Permissions**:

        - To access this API Endpoint, the User must possess one of the following roles: `Admin`, `Contributor`, or `Reader`.

    - **Request Body**:

        - `None`:

    - **Response**:

        - `list[Users]`: A list containing all of the Users saved in the DataBase that the user is authorized to see.
    """
    if user.get("role").casefold() == "admin":
        users = db.query(Users).all()
    else:
        user = db.query(Users).filter(Users.id == user.get("id")).first()
        users = []
        users.append(user)

    for user in users:
        user.hashed_password = ""

    return users


@router.post(
    "/users", status_code=status.HTTP_201_CREATED, responses={400: {"model": Message}}
)
async def create_user(
    db: db_dependency, user: user_dependency, user_request: CreateUserRequest
):
    """
    ## Creates a User

    This endpoint allows you to create a new user.

    - **Permissions**:

        - To access this API Endpoint, the User must possess the following role: `Admin`.

    - **Request Body**:
        - `username`: The Username for the User.

        - `password`: The Password for the User.

        - `role`: The Role for the User.

        - `active`: True if the User is active.

    - **Response**:

        - `None`.
    """

    # Permission Validation
    if user.get("role").casefold() != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"The user '{user.get("username")}' doesn't have permission to create new Users.",
        )

    # Role Validation
    if (
        user_request.role.lower() != "admin"
        and user_request.role.lower() != "contributor"
        and user_request.role.lower() != "reader"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The role '{user_request.role}' is invalid. Only 'Admin', 'Contributor' or 'Reader' are available!",
        )
    # User duplicate Validation
    if db.query(Users).filter(Users.username == user_request.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The user with username '{user_request.username}' already exists!",
        )
    user_model = Users(
        username=user_request.username,
        hashed_password=bcrypt_context.hash(user_request.password),
        role=user_request.role,
        active=True,
    )

    db.add(user_model)
    db.commit()


@router.post(
    "/users/new-superadmin",
    status_code=status.HTTP_201_CREATED,
    responses={403: {"model": Message}},
)
async def create_superadmin(db: db_dependency, user_request: CreateSuperAdminRequest):
    """
    ## Creates a SuperAdmin

    This endpoint allows you to create a new SuperAdmin. <ins>**This only works for the first time running the Application**</ins>.


    - **Request Body**:

        - `password`: The Password for the User.

    - **Response**:

        - `None`.
    """

    user = db.query(Users).filter(Users.username == "superadmin").first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The SuperAdmin has already been created.",
        )

    user_model = Users(
        username="SuperAdmin",
        hashed_password=bcrypt_context.hash(user_request.password),
        role="admin",
        active=True,
    )

    db.add(user_model)
    db.commit()


@router.put(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={400: {"model": Message}},
)
async def update_user(
    db: db_dependency,
    user: user_dependency,
    user_request: UserUpdateRequest,
    user_id: int = Path(gt=0),
):
    """
    ## Updates a User

    This endpoint allows you to update an existing user's password. **Admins** can change every user, while **Contributors** and **Readers** can only update their own passwords.

    - **Permissions**:

        - To access this API Endpoint, the User must possess one of the following roles: `Admin`, `Contributor`, or `Reader`.

    - **Parameters**:

        - `user_id`: The ID of the User.

    - **Request Body**:

        - `password`: The New Password for the User.

    - **Response**:

        - `None`.
    """

    user_model = db.query(Users).filter(Users.id == user_id).first()

    # Permission Validation
    if user.get("role").casefold() != "admin" and user_model.id != user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"The user '{user.get("username")}' doesn't have permission to edit user '{user_model.username}'",
        )

    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The user with ID '{user_id}' was not found.",
        )

    if user_request.password:
        user_model.hashed_password = bcrypt_context.hash(user_request.password)

    if user_request.active:
        user_model.active = user_request.active

    db.add(user_model)
    db.commit()


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={400: {"model": Message}},
)
async def delete_user(
    db: db_dependency, user: user_dependency, user_id: int = Path(gt=0)
):
    """
    ## Deletes a User

    This endpoint allows you to delete an existing user.

    - **Permissions**:

        - To access this API Endpoint, the User must possess the following role: `Admin`.

    - **Parameters**:

        - `user_id`: The ID of the User.

    - **Response**:

        - `None`.
    """

    # Permission Validation
    if user.get("role").casefold() != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"The user '{user.get("username")}' doesn't have permission to create new Users.",
        )

    user_model = db.query(Users).filter(Users.id == user_id).first()
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The user with user ID '{user_id}' doesn't exist!",
        )
    db.delete(user_model)
    db.commit()
