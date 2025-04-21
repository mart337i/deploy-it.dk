import logging
from enum import Enum
from pydantic import BaseModel


class Authtype(str,Enum):
    token="token"
    password="password"
