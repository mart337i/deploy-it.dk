import logging
from enum import Enum
from pydantic import BaseModel

_logger = logging.getLogger(__name__)

class TokenAuth(BaseModel):
    host : str
    user : str
    token_name : str
    token_value : str
    verify_ssl : bool
    auth_type : str
