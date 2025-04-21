import logging
from typing import Any, Dict, List
from urllib.parse import quote

from proxmox.enums.status import StatusCode
from proxmox.utils.exceptions import InvalidConfiguration
from proxmoxer.core import ResourceException
from proxmox.service.task import TaskManagement

from clicx.config import configuration
from clicx.utils.security import _generate_password

_logger = logging.getLogger(__name__)

#######################
# MARK: VM Creation
#######################
class VirtualMachineManagement():

    def __init__(self, connection):
        self._proxmoxer  = connection

    def clone_vm(self, node: str, config: Dict[str, Any]) -> str:
        tasks = []
        msg = []
        new_vmid = self.get_next_available_vm_id()
        task_management = TaskManagement(self._proxmoxer)

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
            full=1
        )

        tasks.append(task_management.blocking_status(node=node,task_id=clone_vm))
        password = _generate_password(8)
        self._proxmoxer.nodes(node).qemu(new_vmid).config.put(
            ciuser = config.get("ciuser"),
            cipassword = password,
            sshkeys = ssh,
        )

        
        task = self.resize_disk(node=node,vm_id=new_vmid,disk_name=disk,size=f'{disk_size}G')
        task_management.blocking_status(node=node,task_id=task)

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