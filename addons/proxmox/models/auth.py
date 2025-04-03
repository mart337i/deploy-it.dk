import logging
from enum import Enum

_logger = logging.getLogger(__name__)

#######################
# MARK: Class Definition and Initialization
#######################

class Authtype(str,Enum):
    token="token"
    password="password"