
import logging

_logger = logging.getLogger(__name__)

class SSLManagement():
    def __init__(self, connection):
        self._proxmoxer  = connection

