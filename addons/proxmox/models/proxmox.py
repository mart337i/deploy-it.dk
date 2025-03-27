from typing import Dict, Any, List, Optional, Union
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException
from clicx.utils.security import _generate_password
from clicx.utils.exceptions import SleepyDeveloperError
from pydantic import BaseModel
import time
from enum import Enum
from pydantic import BaseModel

import logging
_logger = logging.getLogger("proxmox")

#######################
# MARK: Class Definition and Initialization
#######################

class Authtype(str,Enum):
    token="token"
    password="password"

class BackendType(str,Enum):
        local = "local"
        https = "https"
        openssh = "openssh"
        ssh_paramiko = "ssh_paramiko"

class TokenAuth(BaseModel):
    host : str
    user : str
    token_name : str
    token_value : str
    verify_ssl : bool
    auth_type : str

class proxmox:
    """Base class for interacting with Proxmox VE via the proxmoxer API."""

    def __init__(
            self,
            host: str,
            auth_type : Authtype, 
            user : str,
            token_name = False,
            token_value = False,
            password = False,
            backend : BackendType ="https",
            verify_ssl = False
        ):
        """
        Initialize the proxmox class.
        
        Args:
            host: Hostname or IP address of the Proxmox server
            user: Username for authentication
            password: Password for authentication
            verify_ssl: Whether to verify SSL certificates (default: True)
        """

        if auth_type == Authtype.token:
            self._proxmoxer = ProxmoxAPI(
                host=host,
                backend = backend,
                user=user,
                token_name = token_name,
                token_value=token_value,
                verify_ssl=verify_ssl
            )
        elif auth_type == Authtype.password:
            self._proxmoxer = ProxmoxAPI(
                host=host,
                backend = backend,
                user = user,
                password=password,
                verify_ssl=verify_ssl
            )
        else: 
            raise SleepyDeveloperError("missing auth type")
        
        self._host = host

    @property
    def host(self) -> str:
        """Get the host address."""
        return self._host
    
    @property
    def proxmoxer(self) -> ProxmoxAPI:
        """Get the proxmoxer API instance."""
        return self._proxmoxer
    
#######################
# MARK: VM Creation and Configuration
#######################
    def create_vm(self, node: str, config: Dict[str, Any]) -> str:
        """
        Create a virtual machine with the given configuration.
        
        Args:
            node: Node name
            config: VM configuration parameters
            
        Returns:
            Task ID for the creation task
        """
        return self._proxmoxer.nodes(node).qemu.create(**config)
    
    def create_vm_pre_config(self, node: str, sshkeys: str, config: Dict[str, Any]) -> Dict[str, Any]:
        config = config.get('config', {})

        if not config.get('vmid'):
            config['vmid'] = self._proxmoxer.cluster.nextid.get()
        vm_id = config['vmid']

        # Generate a secure password if not provided
        if not config.get('cipassword'):
            config['cipassword'] = _generate_password()
            _logger.info(f"Generated secure password for VM {config.get('vmid')}")

        default_values = {
            'name': f"vm-{vm_id}",
        }
        
        # Merge defaults with provided config
        vm_params = {**default_values, **config}

        # NOTE: It's very important that sshkeys are placed after the ciuser
        # because if placed under cicustom it will be set on the root user
        # as cicustom is executed as root. It would therefore set ssh keys for root instead of the user.
        vm_params['sshkeys'] = sshkeys
        
        vm = self._proxmoxer.nodes(node).qemu.create(
            vmid=vm_id,
            **vm_params
        )
        _logger.debug(f"VM creation task: {vm} for VM ID: {vm_id}")

        # Resize disk
        try:
            self.await_function_completion(self.resize_vm_disk,(node,vm_id,vm_params['scsi0'],vm_params['disk_size']))
        except Exception as e:
            _logger.error(f"Error resizing disk for VM {vm_id}: {e}")
            raise

        return {
            "task":{
                "taskID": vm,
            },
            "vm" : {
                "id": vm_id,
            }
        }

#######################
# MARK:VM Management
#######################

    def resize_vm_disk(self, node,vm_id,disk,new_size):
        try:
            res = self._proxmoxer.nodes(node).qemu(vm_id).resize.put(disk=disk, size=new_size)
            self.await_task_completion(node, res)
        except Exception as e:
            _logger.error(f"Error resizing disk for VM {vm_id}: {e}")
            raise

        return {
            "vm" : {
                "id": vm_id,
                "taskID": res,
                "disk_size": new_size
            }
        }

    def list_vms(self, node: str, **kwargs) -> List[Dict[str, Any]]:
        """List all VMs on a node."""
        return self._proxmoxer.nodes(node).qemu.get(**kwargs)

    def delete_vm(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Delete a VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).delete(**kwargs)

    def clone_vm(self, node: str, vmid: str, newid: str, **kwargs) -> Dict[str, Any]:
        """Clone a VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).clone.post(newid=newid, **kwargs)

    def start_vm(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Start a VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).status.start.post(**kwargs)

    def stop_vm(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Stop a VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).status.stop.post(**kwargs)

    def shutdown_vm(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Shutdown a VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).status.shutdown.post(**kwargs)

    def reset_vm(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Reset a VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).status.reset.post(**kwargs)

    def reboot_vm(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Reboot a VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).status.reboot.post(**kwargs)

    def suspend_vm(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Suspend a VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).status.suspend.post(**kwargs)

    def resume_vm(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Resume a VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).status.resume.post(**kwargs)
    
    
#######################
# MARK: VM Listing and Information
#######################   


    def list_all_vm_ids(self):
        nodes = []
        node_vm_mapping = []

        for node in self.list_nodes():
            node_name = node.get("node")
            nodes.append(node_name)
            
            vm_ids = []
            for vm in self.list_vms(node=node_name):
                vm_ids.append(vm)
            
            vm_ids.sort(key=lambda vm: vm['vmid'])
            node_vm_mapping.append({"Node": node_name, "vm_ids": vm_ids})
            
    def get_vm_ids(self, node: str, **kwargs) -> List[str]:
        """
        Get a list of VM IDs on a node.
        
        Args:
            node: Node name
            kwargs: Additional parameters to pass to the API
            
        Returns:
            List of VM IDs
        """
        vms = self._proxmoxer.nodes(node).qemu.get(**kwargs)
        vm_ids = []
        for vm in vms:
            vmid = vm.get('vmid')
            if vmid:
                vm_ids.append(vmid)
        return vm_ids
    
    def get_vm_status(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Get VM status."""
        return self._proxmoxer.nodes(node).qemu(vmid).status.current.get(**kwargs)

    def get_vm_config(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Get VM configuration."""
        return self._proxmoxer.nodes(node).qemu(vmid).config.get(**kwargs)
    
    def get_next_available_vm_id(self) -> str:
        """
        Get the next available VM ID.
        
        Returns:
            Next available VM ID
        """
        return self._proxmoxer.cluster.nextid.get()
    
#######################
# MARK: Task Management
#######################
    def await_task_completion(self, node: str, upid: str, timeout: int = 300, interval: int = 5) -> Dict[str, Any]:
        """
        Wait for a task to complete.
        
        Args:
            node: Node name
            upid: Task ID
            timeout: Maximum time to wait in seconds
            interval: Time between checks in seconds
            
        Returns:
            Final task status
            
        Raises:
            TimeoutError: If the task does not complete within timeout
        """
        start_time = time.time()
        while True:
            status = self.get_task_status(node, upid)
            exit_status = status.get('exitstatus', '')
            
            if exit_status in ['OK', 'TASK ERROR:']:
                return status
                
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Task {upid} did not complete within {timeout} seconds")
                
            _logger.debug(f"Task status: {status}")
            time.sleep(interval)

    def await_function_completion(func, *args, timeout: int = 300, interval: int = 5, **kwargs) -> Any:
        """
        Wait for a function to complete successfully.
        
        Args:
            func: Function to execute and wait for
            *args: Positional arguments to pass to the function
            timeout: Maximum time to wait in seconds
            interval: Time between attempts in seconds
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The return value of the function when successful
            
        Raises:
            TimeoutError: If the function does not complete successfully within timeout
        """
        start_time = time.time()
        
        while True:
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Function {func.__name__} did not complete successfully within {timeout} seconds") from e
                
                _logger.debug(f"Function attempt failed: {str(e)}")
                time.sleep(interval)

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
    
#######################
# MARK: QEMU Agent Management
#######################
    def execute_command(self, node: str, vmid: str, command: str) -> Dict[str, Any]:
        """
        Execute a command on a VM using the QEMU agent.
        
        Args:
            node: Node name
            vmid: VM ID
            command: Command to execute
            
        Returns:
            Command execution response
        """
        response = self._proxmoxer.nodes(node).qemu(vmid).agent('exec').post(command=command)
        return response
    
    def await_qemu_agent_ready(self, node: str, vm_id: str, timeout: int = 300, interval: int = 5) -> bool:
        """
        Waits for the QEMU agent to be ready.
        
        Args:
            node: Node name
            vm_id: Virtual machine ID
            timeout: Maximum time in seconds to wait for the agent to be ready
            interval: Time in seconds between each status check
            
        Returns:
            True if the agent is ready, False if it timed out or encountered an error
        """
        elapsed_time = 0

        while elapsed_time < timeout:
            status = self.get_qemu_agent_status(node, vm_id)
            status_code = status.get('status_code')

            if status_code == 1:
                return True
            elif status_code == -1:
                _logger.error(f"Error checking QEMU agent: {status.get('error_msg')}")
                return False

            time.sleep(interval)
            elapsed_time += interval

        _logger.warning(f"Timeout waiting for QEMU agent on VM {vm_id}")
        return False

    def get_qemu_agent_status(self, node: str, vm_id: str) -> Dict[str, Any]:
        """
        Get the status of the QEMU agent on a VM.
        
        Args:
            node: Node name
            vm_id: VM ID
            
        Returns:
            Status information with status_code (1=ready, 0=not ready, -1=error) and error message if applicable
        """
        try:
            response = self._proxmoxer.nodes(node).qemu(vm_id).agent.post('ping')
            return {
                'status_code': 1,
                'error_msg': response
            }
        except ResourceException as e:
            return {
                'status_code': 0,
                'error_msg': str(e)
            }
        except Exception as e:
            return {
                'status_code': -1,
                'error_msg': str(e)
            }
    
#######################
# MARK: Network Management
#######################
    def get_vm_ipv4(self, node: str, vmid: str) -> Optional[Dict[str, str]]:
        """
        Get the IPv4 address of a VM.
        
        Args:
            node: Node name
            vmid: VM ID
            
        Returns:
            Dictionary with the IPv4 address or None if not found
        """
        try:
            vm_status = self._proxmoxer.nodes(node).qemu(vmid).agent('network-get-interfaces').get()
            for interface in vm_status.get("result", []):
                if interface.get("name") == "eth0":
                    for ip_info in interface.get("ip-addresses", []):
                        if ip_info.get("ip-address-type") == "ipv4":
                            return {
                                'ipv4': ip_info.get("ip-address")
                            }
            _logger.warning(f"IPv4 address not found for VM {vmid}")
            return None
        except Exception as e:
            _logger.error(f"Error getting IPv4 for VM {vmid}: {e}")
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
    
#######################
# MARK: Version and System Information
#######################
    def get_version(self, **kwargs) -> Dict[str, Any]:
        """Get Proxmox VE version."""
        return self._proxmoxer.version.get(**kwargs)

#######################
# MARK: User and Access Management
#######################
    def list_users(self, **kwargs) -> List[Dict[str, Any]]:
        """List all users."""
        return self._proxmoxer.access.users.get(**kwargs)

    def get_user(self, userid: str, **kwargs) -> Dict[str, Any]:
        """Get user details."""
        return self._proxmoxer.access.users(userid).get(**kwargs)

    def create_user(self, userid: str, password: str, **kwargs) -> Dict[str, Any]:
        """Create a user."""
        return self._proxmoxer.access.users.post(userid=userid, password=password, **kwargs)

    def delete_user(self, userid: str, **kwargs) -> Dict[str, Any]:
        """Delete a user."""
        return self._proxmoxer.access.users(userid).delete(**kwargs)

    def list_roles(self, **kwargs) -> List[Dict[str, Any]]:
        """List all roles."""
        return self._proxmoxer.access.roles.get(**kwargs)

    def list_permissions(self, **kwargs) -> List[Dict[str, Any]]:
        """List all permissions."""
        return self._proxmoxer.access.permissions.get(**kwargs)

    def get_access_control_list(self, **kwargs) -> List[Dict[str, Any]]:
        """Get access control list."""
        return self._proxmoxer.access.acl.get(**kwargs)

    def update_access_control_list(self, path: str, roles: str, **kwargs) -> Dict[str, Any]:
        """Update access control list."""
        return self._proxmoxer.access.acl.put(path=path, roles=roles, **kwargs)

#######################
# MARK:Node and Cluster Management
#######################
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

    def get_iso_files(self, node):
        all_isos = []
        
        iso_storages = self.get_iso_storage(node)
        
        for storage in iso_storages:
            storage_id = storage['storage']
            
            try:
                isos = self._proxmoxer.nodes(node).storage(storage_id).content.get(content='iso')
                
                for iso in isos:
                    iso['storage_name'] = storage_id
                
                all_isos.extend(isos)
            except Exception as e:
                print(f"Warning: Could not get ISOs from storage '{storage_id}': {str(e)}")
        
        return all_isos

    def get_storage(self, node, **kwargs):
        return self._proxmoxer.nodes(node).storage.get()
