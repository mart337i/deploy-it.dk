import logging
import time
from typing import Any, Dict, List

_logger = logging.getLogger(__name__)

class TaskManagement():
    def __init__(self, connection):
        self._proxmoxer  = connection


#######################
# MARK: Task Management
#######################

    @staticmethod
    def blocking_status(self,node, task_id, timeout=300, polling_interval=1):
        start_time: float = time.monotonic()
        data = {"status": ""}
        while data["status"] != "stopped":
            data = self._proxmoxer.nodes(node).tasks(task_id).status.get()
            if isinstance(data,list):
                break
            if start_time + timeout <= time.monotonic():
                data = None  # type: ignore
                break

            time.sleep(polling_interval)
        return data

    def get_task_status(self, node: str, upid: str, **kwargs) -> Dict[str, Any]:
        """
        Get the status of a task.
        
        Args:
            node: Node name
            upid: Task ID (e.g., "UPID:pve:000E025D:028DA1F8:664C8128:qmcreate:201:root@pam:")
            kwargs: Additional parameters to pass to the API
            
        Returns:
            Task status information
        """
        return self._proxmoxer.nodes(node).tasks(upid).status.get(**kwargs)
    
    def list_tasks(self, node: str, **kwargs) -> List[Dict[str, Any]]:
        """List all tasks on a node."""
        return self._proxmoxer.nodes(node).tasks.get(**kwargs)

    def get_task_logs(self, node: str, upid: str, **kwargs) -> List[Dict[str, Any]]:
        """Get task logs."""
        return self._proxmoxer.nodes(node).tasks(upid).log.get(**kwargs)
    