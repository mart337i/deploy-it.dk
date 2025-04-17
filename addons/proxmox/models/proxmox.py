import logging
import time
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, quote_plus

import yaml
import invoke
import paramiko
import urllib3.util
import base64
import uuid
from proxmoxer import ProxmoxAPI
from proxmoxer.backends.https import Backend
from proxmoxer.core import ResourceException
from proxmoxer.tools.tasks import Tasks
from pydantic import BaseModel

from clicx.config import configuration
from clicx.utils.exceptions import SleepyDeveloperError
from clicx.utils.security import _generate_password
from clicx.utils.jinja import render

from proxmox.utils.yml_parser import read
from proxmox.models.auth import Authtype
from proxmox.models.enums import StatusCode,BackendType,QemuStatus
from proxmox.utils.exceptions import InvalidConfiguration

from clicx.utils.jinja import render_from_string,load_template

_logger = logging.getLogger(__name__)

#######################
# MARK: Class Definition and Initialization
#######################

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
        self.available_nodes = list(configuration.loaded_config.get("available_nodes"))

    @property
    def host(self) -> str:
        """Get the host address."""
        return self._host
    
    @property
    def proxmoxer(self) -> ProxmoxAPI:
        """Get the proxmoxer API instance."""
        return self._proxmoxer
    
#######################
# MARK: VM Creation
#######################

    def clone_vm(self, node: str, config: Dict[str, Any]) -> str:
        tasks = []
        msg = []
        new_vmid = self.get_next_available_vm_id()

        available_configuration = configuration.loaded_config.get('vm_configurations')
        chosen_vm_config = available_configuration.get(str(config.get('vmid')))
        clone_id = config.get('vmid')

        if not chosen_vm_config:
            raise InvalidConfiguration("Chould not determine config by the id provided")

        disk_size = chosen_vm_config['hardware'].get("disksize")
        disk = chosen_vm_config['hardware'].get("disk")
        ssh_key = config.get("sshkeys")

        if not disk and not disk_size:
            raise InvalidConfiguration("Chould not determine disk and disk size")


        if not ssh_key: 
            raise ValueError("No ssh key found, Unable to create Vm without it.")

        ssh = quote(config.get("sshkeys"),'')

        clone_vm = self._proxmoxer.nodes(node).qemu(clone_id).clone.create(
            newid=new_vmid,
            name=config.get("name"),
            full=1  # full clone; change to 0 for linked clone if desired.
        )

        tasks.append(self.blocking_status(node=node,task_id=clone_vm))
        password = _generate_password(8)
        self._proxmoxer.nodes(node).qemu(new_vmid).config.put(
            ciuser = config.get("ciuser"),
            cipassword = password,
            sshkeys = ssh,
        )

        
        task = self.resize_disk(node=node,vm_id=new_vmid,disk_name=disk,size=f'{disk_size}G')
        self.blocking_status(node=node,task_id=task)

        self._proxmoxer.nodes(node).qemu(new_vmid).status.start.post()

        return {
            "tasks" : tasks,
            "msg":msg,
            "vm" : {
                "vmid": new_vmid,
                "user" : config.get("ciuser"),
                "password" : password
            }
        }
    
    def create_vm(self, node: str, config: Dict[str, Any]) -> str:
        return self._proxmoxer.nodes(node).qemu.create(**config)
    
    def get_all_configurations(self):
        return configuration.loaded_config.get("vm_configurations")
    
#######################
# MARK: VM Configuration
#######################

    def install_docker_engine(self,node,vmid):
        script = render('install_docker.sh')
        return self.execute_shell_script(script, node, vmid)
    
    def pull_docker_image(self, node, vmid, image_name):
        shell_script = render("pull_image.sh", {
            "image_name":image_name
        })
        
        return self.execute_shell_script(shell_script, node, vmid)

    def start_docker_image(self, node, vmid, image_name, container_name, port_mapping="", volume_mapping="", env_vars=""):
        shell_script = render(
            template_name="start_docker_image.sh",
            context = {
                "image_name": image_name,
                "container_name": container_name,
                "port_mapping": port_mapping,
                "volume_mapping": volume_mapping,
                "env_vars": env_vars
            })


        return self.execute_shell_script(shell_script, node, vmid)

    def stop_docker_image(self, node, vmid, container_name, remove_container=False):
        shell_script = render(
            template_name="stop_docker_image.sh",
            context = {
            "container_name": container_name,
            "remove_container": remove_container
        })
        return self.execute_shell_script(shell_script, node, vmid)
    
    def create_proxy_conf(self, node, vmid, hostname, ip):
        shell_script = render(
            template_name="simple_create_proxy_conf.sh",
            context = {
            "hostname": hostname,
            "ip": ip
        })
        return self.execute_shell_script(shell_script, node, vmid)
    
    def create_proxy_for_docker_conf(self, node, vmid, hostname, ip, port, name):
        shell_script = render(
            template_name="create_proxy_conf.sh",
            context = {
            "hostname": hostname,
            "ip": ip,
            "port" : port,
            "name": name,
        })
        return self.execute_shell_script(shell_script, node, vmid)

    def configure_vm(self, node: str, vmid: str, script_name: str):
        """Execute a predefined shell script template on a VM"""
        # Check Qemu status
        qemu_available = self.await_qemu_agent_ready(node=node, vm_id=vmid)
        if qemu_available != QemuStatus.running:
            raise ResourceException(status_code=500, status_message="Qemu agent not running")
    
        try:
            # Render the script from template
            script_content = render(template_name=script_name)
            
            # Execute the shell script
            result = self.execute_shell_script(script_content=script_content, node=node, vmid=vmid)
            
            # Return job status
            return {
                "status": "completed" if result["status"] == "success" else "failed",
                "node": node,
                "vmid": vmid,
                "script_name": script_name,
                "result": result
            }
        
        except Exception as e:
            _logger.error(f"Failed to configure VM {vmid} on node {node}: {str(e)}")
            raise ResourceException(status_code=500, status_message=f"VM configuration failed: {str(e)}")
    
    def configure_vm_custom(self, node: str, vmid: str, script_file):
        """Execute a custom shell script uploaded by user on a VM"""
        # Check Qemu status
        qemu_available = self.await_qemu_agent_ready(node=node, vm_id=vmid)
        if qemu_available != QemuStatus.running:
            raise ResourceException(status_code=500, status_message="Qemu agent not running")
        
        try:
            # Read the content from the UploadFile object
            script_content = script_file.file.read().decode('utf-8')
            
            # Execute the shell script
            result = self.execute_shell_script(script_content=script_content, node=node, vmid=vmid)
            
            # Return job status
            return {
                "status": "completed" if result["status"] == "success" else "failed",
                "node": node,
                "vmid": vmid,
                "result": result
            }
        
        except Exception as e:
            _logger.error(f"Failed to configure VM {vmid} on node {node}: {str(e)}")
            raise ResourceException(status_code=500, status_message=f"VM configuration failed: {str(e)}")
#######################
# MARK:VM Management
#######################

    def resize_disk(self, node, vm_id, disk_name, size):
        task = self._proxmoxer.nodes(node).qemu(vm_id).resize.put(
            disk=disk_name,
            size=size
        )
        return task

    def list_vms(self, node: str, **kwargs) -> List[Dict[str, Any]]:
        """List all VMs on a node."""
        return self._proxmoxer.nodes(node).qemu.get(**kwargs)
    
    def ping_qemu(self, node: str, vmid: int, **kwargs) -> List[Dict[str, Any]]:
        """Ping QEMU agent for a specific VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).agent.ping.post()

    def delete_vm(self, node: str, vmid: str, **kwargs) -> Dict[str, Any]:
        """Delete a VM."""
        # TODO Write a check to see if the instance is runnning and if it is, shut it down. 
        return self._proxmoxer.nodes(node).qemu(vmid).delete(**kwargs)

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
    
#######################
# MARK: QEMU Agent Management
#######################

    def execute_shell_script(self, script_content: str, node: str, vmid: str):
        """Execute a shell script on the VM using QEMU guest agent"""
        _logger.info(f"Executing shell script on VM {vmid}")
        # Replace script name with a uuid, to make sure it is uniqe
        script_path = "/tmp/proxmox_script.sh"
    
        try:
            # Use the correct file-write endpoint with proper parameters
            self._proxmoxer.nodes(node).qemu(vmid).agent("file-write").post(
                content=script_content,
                file=script_path,
                encode=1
            )
        
            # Make the script executable
            # For the exec endpoint, command should be an array of strings
            chmod_res = self._proxmoxer.nodes(node).qemu(vmid).agent("exec").post(
                command=["chmod", "+x", script_path]
            )
            
            # Wait for chmod to complete
            chmod_status = self._proxmoxer.nodes(node).qemu(vmid).agent("exec-status").get(
                pid=chmod_res.get('pid')
            )
            
            # Check if chmod was successful
            if chmod_status.get('exitcode', 1) != 0:
                raise Exception(f"Failed to make script executable: {chmod_status.get('err-data', '')}")
        
            # Execute the script with sudo
            exec_res = self._proxmoxer.nodes(node).qemu(vmid).agent("exec").post(
                command=["sudo", script_path]
            )
            
            # Poll for completion
            exec_result = None
            while True:
                exec_status = self._proxmoxer.nodes(node).qemu(vmid).agent("exec-status").get(
                    pid=exec_res.get('pid')
                )
                
                # Check if command has exited
                if exec_status.get('exited', False):
                    exec_result = exec_status
                    break
                
                # Wait before polling again
                time.sleep(1)
        
            # Parse the execution result
            stdout = exec_result.get('out-data', '')
            stderr = exec_result.get('err-data', '')
            exit_code = exec_result.get('exitcode', 1)
        
            status = "success" if exit_code == 0 else "failed"
        
            results = {
                "exec_result": exec_result,
                "status": status,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code
            }
        
            # Clean up the script
            cleanup_res = self._proxmoxer.nodes(node).qemu(vmid).agent("exec").post(
                command=["rm", script_path]
            )
            
            # Wait for cleanup to complete
            self._proxmoxer.nodes(node).qemu(vmid).agent("exec-status").get(
                pid=cleanup_res.get('pid')
            )
        
            return results
        
        except Exception as e:
            _logger.error(f"Failed to execute script on VM {vmid}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }


    def execute_command(self, node: str, vmid: str, command: str) -> Dict[str, Any]:
        """
        Execute a command on a VM using the QEMU agent.
        
        NOTE: To execute a sell command the command argument should start with `/bin/sh -c "echo test > /test.file"`
        See: https://forum.proxmox.com/threads/how-to-create-or-edit-file-with-qm-guest-agent.89759/

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
            res = self.get_qemu_agent_status(node, vm_id)
            
            if res["status"] == QemuStatus.running:
                return QemuStatus.running
            
            if res["status"] == QemuStatus.failure:
                raise ValueError(res["exception"])

            time.sleep(interval)
            elapsed_time += interval

        _logger.warning(f"Timeout waiting for QEMU agent on VM {vm_id}")
        return QemuStatus.failure

    def get_qemu_agent_status(self, node: str, vm_id: str) -> Dict[str, Any]:
        try:
            self._proxmoxer.nodes(node).qemu(vm_id).agent.post('ping')
            return {"status" : QemuStatus.running}
        except ResourceException as e:
            return {"status" : QemuStatus.pending}
        except Exception as e:
            return {
                'status': QemuStatus.failure,
                'exception' : e
            }
    
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

    def add_ssh(self,node,vmid,username,key):
        ssh_content = ""
        with open(key,"r") as content:
            ssh_content = content.read()
        try:
            response = self._proxmoxer.nodes(node).qemu(vmid).agent('file-write').post(content=ssh_content,file=f"/home/{username}/.ssh/authorized_keys",node=node,vmid=vmid)
            return {
                'status_code': StatusCode.sucess,
                'msg': response
            }
        except ResourceException as e:
            return {
                'status_code': StatusCode.failure,
                'error_msg': str(e)
            }
        except Exception as e:
            return {
                'status_code': StatusCode.failure,
                'error_msg': str(e)
            }
        
    def get_exec_status(self,node,vmid,pid):

        try:
            response = self._proxmoxer.nodes(node).qemu(vmid).agent('exec-status').get(pid=pid)
            return {
                'status_code': StatusCode.sucess,
                'msg': response
            }
        except ResourceException as e:
            return {
                'status_code': StatusCode.failure,
                'error_msg': str(e)
            }
        except Exception as e:
            return {
                'status_code': StatusCode.failure,
                'error_msg': str(e)
            }