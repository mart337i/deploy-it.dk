
# Third-party imports
from fastapi.routing import APIRouter

from fastapi.routing import APIRouter
from fastapi import HTTPException, File, UploadFile
from typing import Any

from addons.proxmox.schema.virtual_machine import VirtualMachine, VirtualMachineCI
from addons.proxmox.schema.bash import BashCommand

from addons.proxmox.models.proxmox import proxmox, TokenAuth
from addons.proxmox.utils.yml_parser import read as yml_read
from addons.proxmox.utils.yml_parser import validate as yml_validate

from clicx.config import configuration

from urllib.parse import quote


router = APIRouter(
    prefix=f"/proxmox/v1/vm",
    tags=["Virtual machine control"],
)

dependency = []

def pve_conn(
    host: str = configuration.env['host'],
    user: str = configuration.env['user'],
    token_name: str = configuration.env["token_name"],
    token_value: str = configuration.env["token_value"],
    verify_ssl: bool = False,
    auth_type: str = "token",
):
    return proxmox(
        **vars(TokenAuth(
            host=host,
            user=user,
            token_name=token_name,
            token_value=token_value,
            verify_ssl=verify_ssl,
            auth_type=auth_type,
        ))
    )

@router.get(path="/get_vm_ids")
def get_vm_ids(node : str) -> Any:
    return pve_conn().get_vm_ids(node=node)

@router.get(path="/get_next_available_vm_id")
def get_next_available_vm_id() -> Any:
    return {
        "vmid": int(pve_conn().get_next_available_vm_id())
    }

@router.post(path="/create-vm/")
def create_vm(node: str, vm_config: VirtualMachine):
    try:
        config = vm_config.config
        vm = pve_conn().create_vm(node=node,config=config)
        return vm
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-vm-pre-config/")
def create_vm_pre_config(node: str, sshkeys : str, vm_config: VirtualMachineCI):
    """
    This medthod utilizes Cloud init for base configureing the VM
    """
    try:
        sshkeys = quote(sshkeys, safe='')
        vm = pve_conn().create_vm_pre_config(node=node,sshkeys=sshkeys,config=vm_config.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating VM: {e}")
    return vm

@router.post(path="/bash_command")
def execute_command(node : str, vmid : int, command : BashCommand):

    response = pve_conn().bash_command(node=node, vmid=vmid, command=command.command)

    return response

@router.get(path="/get_network_setting_vm")
def get_network_setting_vm(node : str, vmid : int):

    response = pve_conn().get_network_setting_vm(node=node, vmid=vmid)

    return response

@router.get(path="/get_vm_ipv4")
def get_vm_ipv4(node : str, vmid : int):

    response = pve_conn().get_vm_ipv4(node=node, vmid=vmid)
    if response == None:
        raise HTTPException(500, detail=f"Chould not resive ipv4, see API log for more info")
    return response

@router.post("/execute-commands")
async def execute_commands(node: str,vmid: int,file: UploadFile = File(...)) -> dict[str, str] | dict[str, list]:
    commands = yml_read(file)
    if not yml_validate(commands):
        return {"error": "Invalid YAML format. Expected 'runcmd' list."}
    
    responses = []
    for command in commands["commands"]:
        try:
            response = pve_conn.execute_command(node=node, vmid=vmid, command=command)
            responses.append({
                "command": command,
                "status": "success",
                "response": response
            })
        except Exception as e:
            responses.append({
                "command": command,
                "status": "error",
                "error": str(e)
            })
    
    return {"responses": responses}

@router.get("/resize_disk")
def resize_disk(node,vm_id,disk,new_size) -> dict[str, dict[str, Any]]:
    return pve_conn().resize_vm_disk(node=node,vm_id=vm_id,disk=disk,new_size=new_size)

@router.get("/await_task_completion")
def await_task_completion(node: str, upid: str, timeout: int = 300, interval: int = 5):
    return pve_conn().await_task_completion(node=node, upid=upid,timeout=timeout,interval=interval)

@router.get("/get_task_status")
def get_task_status(node: str, upid: str):
    return pve_conn().get_task_status(node=node, upid=upid)

@router.get("/list_tasks")
def list_tasks(node: str):
    return pve_conn().list_tasks(node=node)

@router.get("/get_task_logs")
def get_task_logs(node: str, upid: str):
    return pve_conn().get_task_logs(node=node,upid=upid)

@router.get("/list_vms")
def list_vms(node:str) -> Any:
    return pve_conn().list_vms(node=node)
    
@router.get("/list_all_vm_ids")
def list_all_vm_ids() -> Any:

    return pve_conn().list_all_vm_ids()

@router.get("/get_vm_status")
def get_vm_status(node: str, vmid: str) -> Any:
    return pve_conn().get_vm_status(node=node, vmid=vmid)

@router.get("/get_vm_config")
def get_vm_config(node: str, vmid: str) -> Any:
    return pve_conn().get_vm_config(node=node, vmid=vmid)

@router.delete("/delete_vm")
def delete_vm(node: str, vmid: str) -> Any:
    return pve_conn().delete_vm(node=node, vmid=vmid)

@router.post("/clone_vm")
def clone_vm(newid: str, node: str, vmid: str) -> Any:
    return pve_conn().clone_vm(newid=newid, node=node, vmid=vmid)

@router.post("/start_vm")
def start_vm(node: str, vmid: str) -> Any:
    return pve_conn().start_vm(node=node, vmid=vmid)

@router.post("/stop_vm")
def stop_vm(node: str, vmid: str) -> Any:
    return pve_conn().stop_vm(node=node, vmid=vmid)

@router.post("/shutdown_vm")
def shutdown_vm(node: str, vmid: str) -> Any:
    return pve_conn().shutdown_vm(node=node, vmid=vmid)

@router.post("/reset_vm")
def reset_vm(node: str, vmid: str) -> Any:
    return pve_conn().reset_vm(node=node, vmid=vmid)

@router.post("/reboot_vm")
def reboot_vm(node: str, vmid: str) -> Any:
    return pve_conn().reboot_vm(node=node, vmid=vmid)

@router.post("/suspend_vm")
def suspend_vm(node: str, vmid: str) -> Any:
    return pve_conn().suspend_vm(node=node, vmid=vmid)

@router.post("/resume_vm")
def resume_vm(node: str, vmid: str) -> Any:
    return pve_conn().resume_vm(node=node, vmid=vmid)