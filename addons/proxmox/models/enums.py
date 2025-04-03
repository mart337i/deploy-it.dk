import logging
from enum import Enum, IntEnum

from pydantic import BaseModel

class BackendType(str,Enum):
        local = "local"
        https = "https"
        openssh = "openssh"
        ssh_paramiko = "ssh_paramiko"

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
    