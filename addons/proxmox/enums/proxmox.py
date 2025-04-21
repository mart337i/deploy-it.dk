import logging
from enum import Enum, IntEnum

class BackendType(str,Enum):
        local = "local"
        https = "https"
        openssh = "openssh"
        ssh_paramiko = "ssh_paramiko"