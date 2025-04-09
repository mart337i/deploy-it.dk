from typing import Any

from fastapi import HTTPException, status
from fastapi.routing import APIRouter
from openvpn.models.openvpn import openVpn
from openvpn.schema.client import (ClientRequest, ClientResponse,
                                   RevokeResponse, StatusResponse)

router = APIRouter(
    prefix=f"/vpn/v1",
    tags=["VPN Management"],
)


@router.post("/client", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(client_request: ClientRequest) -> Any:
    """
    Create a new OpenVPN client and return the client configuration.
    """
    try:
        # Check if client already exists
        if openVpn.already_exists(client_request.client_name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Client {client_request.client_name} already exists"
            )
        
        # Create the client
        client_config = openVpn.create_client(client_request.client_name)
        
        return {
            "client_name": client_request.client_name,
            "config": client_config,
            "message": f"VPN client {client_request.client_name} created successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create VPN client: {str(e)}"
        )

@router.get("/client/{client_name}", response_model=StatusResponse)
def check_client(client_name: str) -> Any:
    """
    Check if a client exists
    """
    try:
        exists = openVpn.already_exists(client_name)
        
        if exists:
            return {
                "exists": True,
                "client_name": client_name,
                "message": f"Client {client_name} exists"
            }
        else:
            return {
                "exists": False,
                "client_name": client_name,
                "message": f"Client {client_name} does not exist"
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check client status: {str(e)}"
        )

@router.delete("/client/{client_name}", response_model=RevokeResponse)
def revoke_client(client_name: str) -> Any:
    """
    Revoke an OpenVPN client certificate
    """
    try:
        # Check if client exists first
        if not openVpn.already_exists(client_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client {client_name} does not exist"
            )
        
        # Revoke the client
        openVpn.revoke_client(client_name)
        
        return {
            "client_name": client_name,
            "message": f"VPN client {client_name} revoked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke client: {str(e)}"
        )

@router.get("/")
def get_info() -> Any:
    return {
        "service": "OpenVPN",
        "endpoints": {
            "create_client": "POST /vpn/v1/client",
            "check_client": "GET /vpn/v1/client/{client_name}",
            "revoke_client": "DELETE /vpn/v1/client/{client_name}",
        },
        "version": "1.0"
    }