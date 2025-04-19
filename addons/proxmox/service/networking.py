import logging
from typing import Any, Dict, List, Optional
from proxmox.service.proxmox import Proxmox
from proxmoxer import ProxmoxAPI

_logger = logging.getLogger(__name__)

class NetworkManagment():

    def __init__(self, connection) -> Proxmox:
        self._proxmoxer : ProxmoxAPI = connection


#######################
# MARK: Network Management
#######################

    def get_vm_ip(self, node: str, vmid: str) -> Optional[Dict[str, str]]:
        """
        Get the IP address of a VM.
        
        Args:
            node: Node name
            vmid: VM ID
            
        Returns:
            Dictionary with the IP address or None if not found
        """
        try:
            vm_status = self._proxmoxer.nodes(node).qemu(vmid).agent('network-get-interfaces').get()
            for interface in vm_status.get("result", []):
                if interface.get("name") == "eth0":
                    for ip_info in interface.get("ip-addresses", []):
                        return {
                            'ip': ip_info.get("ip-address")
                        }

            _logger.warning(f"IP address not found for VM {vmid}")
            return None
        except Exception as e:
            _logger.error(f"Error getting IP for VM {vmid}: {e}")
            return None
    
    def get_network_setting_vm(self, node: str, vmid: str) -> Dict[str, Any]:
        """
        Get network settings for a VM.
        
        Args:
            node: Node name
            vmid: VM ID
            
        Returns:
            Network settings information
        """
        return self._proxmoxer.nodes(node).qemu(vmid).agent('network-get-interfaces').get()
    
    def map_hostname_and_ip(self) -> List[Dict[str, str]]:
        """
        Map hostnames to IP addresses for all nodes.
        
        Returns:
            List of dictionaries with hostname and IP address
        """
        hostname_to_ip_list = []

        for node in self._proxmoxer.nodes.get():
            node_name = node['node']
            try:
                network_config = self._proxmoxer.nodes(node_name).network.get()
                ip_addresses = [iface['address'] for iface in network_config if 'address' in iface]
                
                if ip_addresses:
                    hostname_to_ip_list.append({
                        'hostname': node_name, 
                        'ip_address': ip_addresses[0]  # Use first IP address
                    })
            except Exception as e:
                _logger.error(f"Error getting network config for node {node_name}: {e}")

        return hostname_to_ip_list

    def get_node_network_config(self, node: str) -> List[Dict[str, Any]]:
        """
        Get network configuration for a node.
        
        Args:
            node: Node name
            
        Returns:
            Network configuration
        """
        return self._proxmoxer.nodes(node).network.get()