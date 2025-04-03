import os
import subprocess
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Response, status
from fastapi.responses import FileResponse
from openvpn.models.openvpn import openVpn
from openvpn.schema.client import ClientCreate, ClientList, ClientResponse
from pydantic import BaseModel

from clicx.utils.jinja import _env

router = APIRouter(
    prefix="/openvpn",
    tags=["OpenVPN creation and configuration"],
)

dependency = []

@router.post("/clients/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(client: ClientCreate):
    """Create a new OpenVPN client certificate."""
    try:
        openVpn.create_client(client.name)
        return ClientResponse(name=client.name, created_at=datetime.now())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clients/{client_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_name: str):
    """Revoke and delete a client certificate."""
    try:
        openVpn.delete_client(client_name)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients/{client_name}/exists", response_model=dict)
async def exists(client_name: str):
    """Check if a client certificate exists."""
    try:
        exists = openVpn.exists(client_name)
        return {"name": client_name, "exists": exists}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients/", response_model=ClientList)
async def list_clients():
    """List all client certificates."""
    try:
        clients = openVpn.get_existing()
        client_list = [ClientResponse(name=client) for client in clients]
        return ClientList(clients=client_list, count=len(client_list))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
