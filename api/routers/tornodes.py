from fastapi import APIRouter, HTTPException, Depends, Path
import requests
from starlette import status
from api.routers.schemas import Message, CreateIPAddressRequest
from api.models import IPAddress
from api.database import get_database
from .auth import get_current_user
from typing import Annotated
from sqlalchemy.orm import Session
import ipaddress

router = APIRouter(
    prefix="/tor-nodes",
    tags=["tor-nodes"],
)

db_dependency = Annotated[Session, Depends(get_database)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get(
    "/external-all", status_code=status.HTTP_200_OK, responses={403: {"model": Message}}
)
def get_external_exit_nodes(user: user_dependency) -> list:
    """
    ## Gets the IP Addresses from External Sources

    This endpoint allows you to get the Exit Nodes from External Sources.

    - **Permissions**:

        - To access this API Endpoint, the User must possess one of the following roles: `Admin`, `Contributor`, or `Reader`.

    - **Response**:

        - `list[str]`: A list containing all the IP Addresses from the External Sources.
    """

    response = requests.get(url="https://www.dan.me.uk/torlist/?exit")

    try:
        response.raise_for_status()
    except requests.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The external sources only allows you to get the data once every 30 minutes.",
        )
    else:
        # Returns a List of all the IP Addresses
        return response.text.split("\n")


@router.post(
    "/exemptions",
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": Message}},
)
def create_exemptions(
    db: db_dependency, user: user_dependency, exemption_request: CreateIPAddressRequest
) -> None:
    """
    ## Add a TOR IP Address Exemption

    This endpoint allows you to add a new IP Address as an exemption for the list of Exit routes that TOR uses. Duplicate entries will be skipped.

    - **Permissions**:

        - To access this API Endpoint, the User must possess one of the following roles: `Admin` or `Contributor`.

    - **Request Body**:
        - `ipaddress`: The IP Address that will be exempted.

    - **Response**:
        - `None`
    """

    if (
        user.get("role").casefold() != "admin"
        and user.get("role").casefold() != "contributor"
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"The user '{user.get("username")}' doesn't have permission to create new Users.",
        )

    try:
        ipaddress.ip_address(exemption_request.ipaddress)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The IP Address '{exemption_request.ipaddress}' is invalid.",
        )
    else:
        if (
            db.query(IPAddress)
            .filter(IPAddress.ipaddress == exemption_request.ipaddress)
            .first()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The IP Address '{exemption_request.ipaddress}' already exists.",
            )
        ip_model = IPAddress(**exemption_request.model_dump())
        db.add(ip_model)
        db.commit()


@router.get("/exemptions", status_code=status.HTTP_200_OK)
def get_exemptions(db: db_dependency, user: user_dependency) -> None:
    """
    ## Gets all the TOR IP Address Exemption

    This endpoint allows you to get all of the IP Address that are exempted from the list of Exit routes that TOR uses.

    - **Permissions**:

        - To access this API Endpoint, the User must possess one of the following roles: `Admin`, `Contributor`, or `Reader`.

    - **Request Body**:
        - `None`

    - **Response**:
        - `list[IPAddress]`: The complete List of all the Exempted IP Addresses.
    """

    all_exemptions = db.query(IPAddress).all()

    return all_exemptions


@router.delete(
    "/exemptions/{ip_address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": Message}},
)
async def delete_exemption(
    db: db_dependency, user: user_dependency, ip_address_id: int = Path(gt=0)
):
    """
    ## Deletes a TOR IP Address Exemption

    This endpoint allows you to delete an IP Address from the exemption list of Exit routes that TOR uses.

    - **Permissions**:

        - To access this API Endpoint, the User must possess one of the following roles: `Admin` or `Contributor`.

    - **Request Body**:
        - `ip_address_id`: The IP Address ID that will be used for deletion.

    - **Response**:
        - `None`
    """

    if (
        user.get("role").casefold() != "admin"
        and user.get("role").casefold() != "contributor"
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"The user '{user.get("username")}' doesn't have permission to create new Users.",
        )

    ip_address = db.query(IPAddress).filter(IPAddress.id == ip_address_id).first()

    if not ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The IP Address with ID '{ip_address_id}' was not found.",
        )

    db.delete(ip_address)
    db.commit()


@router.get("/external-filtered-exemptions")
def get_external_exit_nodes_filtered(db: db_dependency, user: user_dependency) -> list:
    """
    ## Gets the IP Addresses from External Sources (Filtered)

    This endpoint allows you to get the Exit Nodes from External Sources without the exempted IP Addresses.

    - **Permissions**:

        - To access this API Endpoint, the User must possess one of the following roles: `Admin`, `Contributor`, or `Reader`.

    - **Response**:

        - `list[str]`: A list containing all the IP Addresses from the External Sources.
    """

    all_external_ips = get_external_exit_nodes(user)
    all_exemptions = db.query(IPAddress).all()

    for exemption in all_exemptions:
        try:
            all_external_ips.remove(exemption.ipaddress)
        except ValueError:
            pass

    return all_external_ips
