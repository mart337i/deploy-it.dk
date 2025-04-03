import logging
from enum import Enum
from pydantic import BaseModel

_logger = logging.getLogger(__name__)

#######################
# MARK: Class Definition and Initialization
#######################

class Authtype(str,Enum):
    token="token"
    password="password"

class TokenAuth(BaseModel):
    host : str
    user : str
    token_name : str
    token_value : str
    verify_ssl : bool
    auth_type : str
