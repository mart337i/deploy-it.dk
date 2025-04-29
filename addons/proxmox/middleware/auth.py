from fastapi import Request
from fastapi.exceptions import HTTPException

from clicx.config import configuration

import logging
_logger = logging.getLogger(__name__)

async def pass_through_authentication(request: Request):
    auth_header = request.headers.get("Authorization")
    token = configuration.env.get('token_value', False)
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing authorization header")
    
    if not token:
        raise HTTPException(status_code=500, detail="API is missing proxmox token")
    
    request_token = auth_header.replace("Bearer ", "")
    
    if request_token != token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")