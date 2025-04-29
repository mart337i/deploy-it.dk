from pydantic import BaseModel, Field
from typing import Optional
from typing import Dict, Any, Optional, List

class Task(BaseModel):
    task: str = Field(..., description="The task ID for the operation")
    
    class Config:
        extra = 'forbid'
        json_schema_extra = {
            "example": {
                "task": "UPID:node1:001219AA:0306C75E:6810AEC0:<command>:101:api@pam!API-Token:"
            }
        }

