import logging
from typing import Any, Dict, List

_logger = logging.getLogger(__name__)

class ClusterManagement():

    def __init__(self, connection):
        self._proxmoxer  = connection

    def list_nodes(self, **kwargs) -> List[Dict[str, Any]]:
        """List all nodes."""
        return self._proxmoxer.nodes.get(**kwargs)

    def get_node_status(self, node: str, **kwargs) -> Dict[str, Any]:
        """Get node status."""
        return self._proxmoxer.nodes(node).status.get(**kwargs)

    def list_resources(self, **kwargs) -> List[Dict[str, Any]]:
        """List all resources."""
        return self._proxmoxer.cluster.resources.get(**kwargs)
    