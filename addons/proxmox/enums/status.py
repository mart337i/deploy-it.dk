import logging
from enum import Enum, IntEnum

class StatusCode(IntEnum):
    sucess = 0
    failure = 1
    def __str__(self):
        return f"{self.value}"
    def __repr__(self):
        return f"{self.value}"