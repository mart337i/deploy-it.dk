from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel

class ClientResponse(BaseModel):
    name: str
    created_at: Optional[datetime] = None
    status: str = "active"
    
class ClientList(BaseModel):
    clients: List[ClientResponse]
    count: int

class ClientCreate(BaseModel):
    name: str