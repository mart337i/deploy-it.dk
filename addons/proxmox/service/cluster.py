import logging
from typing import Any, Dict, List
from proxmox.service.proxmox import Proxmox
from proxmoxer import ProxmoxAPI

_logger = logging.getLogger(__name__)

class ClusterManagement():

    def __init__(self, connection) -> Proxmox:
        self._proxmoxer : ProxmoxAPI = connection

    def list_nodes(self, **kwargs) -> List[Dict[str, Any]]:
        """List all nodes."""
        return self._proxmoxer.nodes.get(**kwargs)

    def get_node_status(self, node: str, **kwargs) -> Dict[str, Any]:
        """Get node status."""
        return self._proxmoxer.nodes(node).status.get(**kwargs)

    def list_resources(self, **kwargs) -> List[Dict[str, Any]]:
        """List all resources."""
        return self._proxmoxer.cluster.resources.get(**kwargs)
    
    def get_iso_storage(self, node):
        storages = self._proxmoxer.nodes(node).storage.get()
        iso_storages = [
            storage for storage in storages 
            if 'content' in storage and 'iso' in storage['content'].split(',')
        ]
        
        return iso_storages