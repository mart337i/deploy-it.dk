import logging
from enum import Enum, IntEnum

from pydantic import BaseModel

class Authtype(str,Enum):
    token="token"
    password="password"

class BackendType(str,Enum):
        local = "local"
        https = "https"
        openssh = "openssh"
        ssh_paramiko = "ssh_paramiko"

class TokenAuth(BaseModel):
    host : str
    user : str
    token_name : str
    token_value : str
    verify_ssl : bool
    auth_type : str

class StatusCode(IntEnum):
    sucess = 0
    failure = 1
    def __str__(self):
        return f"{self.value}"
    def __repr__(self):
        return f"{self.value}"
    
class QemuStatus(str,Enum):
    running = "Running"
    pending = "Pending"
    failure = "Failure"
    
    def __str__(self):
        return f"{self.value}"
    def __repr__(self):
        return f"{self.value}"
    