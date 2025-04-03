
from typing import Annotated, Any

import validators
from fastapi import File, HTTPException, UploadFile
from fastapi.routing import APIRouter
from proxmox.models.enums import TokenAuth
from proxmox.models.proxmox import proxmox
from proxmox.schema.bash import BashCommand
from proxmox.schema.vm import CloneVM, VirtualMachine
from proxmox.utils.yml_parser import read as yml_read
from proxmox.utils.yml_parser import validate as yml_validate

from clicx.config import configuration

router = APIRouter(
    prefix=f"/proxmox/v1/vm",
    tags=["Virtual machine control"],
)

dependency = []

def pve_conn(
    host: str = configuration.loaded_config['host'],
    user: str = configuration.loaded_config['user'],
    token_name: str = configuration.loaded_config["token_name"],
    token_value: str = configuration.loaded_config["token_value"],
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

@router.get(path="/get_all_configurations")
def get_all_configurations() -> Any:
    return pve_conn().get_all_configurations()

@router.get(path="/get_software_configurations")
def get_software_configurations() -> Any:
    return pve_conn().get_software_configurations()

@router.get(path="/get_next_available_vm_id")
def get_next_available_vm_id() -> Any:
    return {
        "vmid": int(pve_conn().get_next_available_vm_id())
    }

@router.post(path="/configure_vm")
def configure_vm(node : str, vmid: int, config_name : str):
    return pve_conn().configure_vm(node=node,vmid=vmid,script_name=config_name)

@router.post(path="/configure_vm_custom")
def configure_vm_custom(node : str, vmid: int, config_file : UploadFile = File(...)):
    return pve_conn().configure_vm_custom(node=node,vmid=vmid,script_file=config_file)

@router.post(path="/clone-vm")
def clone_vm(node: str, vm_config: CloneVM):
    if not validators.hostname(vm_config.name):
        raise HTTPException(422, "Invalid Hostname")
    
    return pve_conn().clone_vm(node=node,config=vm_config.model_dump())
    
@router.post(path="/create-vm")
def create_vm(node: str, vm_config: VirtualMachine):
    try:
        config = vm_config.config
        vm = pve_conn().create_vm(node=node,config=config)
        return vm
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(path="/get_vm_ip")
def get_vm_ip(node : str, vmid : int):

    response = pve_conn().get_vm_ip(node=node, vmid=vmid)
    if response == None:
        raise HTTPException(500, detail=f"Chould not resive ip, see API log for more info")
    return response

@router.get(path="/ping_qemu")
def ping_qemu(node : str, vmid : int):

    response = pve_conn().ping_qemu(node=node, vmid=vmid)
    if response == None:
        raise HTTPException(500, detail=f"Failed to ping QEMU guest agent")
    return response

@router.get(path="/get_qemu_agent_status")
def get_qemu_agent_status(node : str, vmid : int):
    response = pve_conn().get_qemu_agent_status(node=node,vm_id=vmid)
    return response

@router.put("/resize_disk")
def resize_disk(node: str,vm_id: int,disk: str,new_size: str):
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