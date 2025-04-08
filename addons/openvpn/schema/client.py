from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from validators import hostname

class ClientResponse(BaseModel):
    client_name: str
    config: str
    message: str

class RevokeResponse(BaseModel):
    client_name: str
    message: str

class StatusResponse(BaseModel):
    exists: bool
    client_name: Optional[str] = None
    message: str

class ClientRequest(BaseModel):
    client_name: str = Field(..., description="Name of the VPN client to create")
    
    @field_validator('client_name')
    def validate_client_name(cls, v):
        if not hostname(v):
            raise ValueError("Invalid client name. Must be a valid hostname.")
        return v