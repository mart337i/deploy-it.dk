from enum import Enum

class QemuStatus(str,Enum):
    running = "Running"
    pending = "Pending"
    failure = "Failure"
    
    def __str__(self):
        return f"{self.value}"
    def __repr__(self):
        return f"{self.value}"