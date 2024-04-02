from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    message: str

    class Config:
        json_schema_extra = {"example": {"detail": "An error ocurred!"}}


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str
    active: bool

    class Config:
        json_schema_extra = {
            "example": {
                "username": "agustin",
                "password": "supersecret",
                "role": "admin",
                "active": True,
            }
        }


class CreateSuperAdminRequest(BaseModel):
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "password": "supersecret",
            }
        }


class CreateIPAddressRequest(BaseModel):
    ipaddress: str

    class Config:
        json_schema_extra = {"example": {"ipaddress": "8.8.8.8"}}


class UserUpdateRequest(BaseModel):
    password: Optional[str] = None
    active: Optional[bool] = None

    class Config:
        json_schema_extra = {"example": {"password": "anotherPassword"}}
