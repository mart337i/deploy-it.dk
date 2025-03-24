from datetime import datetime

# Third-party imports
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter

from fastapi.routing import APIRouter
from fastapi import HTTPException, Request, File, UploadFile
from typing import Any, Dict

from addons.proxmox.schema.virtual_machine import VirtualMachine, VirtualMachineCI
from addons.proxmox.schema.bash import BashCommand
from addons.proxmox.schema.lxc import Container

from addons.proxmox.models.proxmox import proxmox

import os

import yaml

from datetime import timedelta

from urllib.parse import quote


router = APIRouter(
    prefix=f"/proxmox/v1/vm",
    tags=["Virtual machine control"],
)

dependency = []

def call_proxmox() -> proxmox:
    """
    Create a connection to proxmox via an api wrapper proxAPI, witch then implements proxmoxer
    
    """

    return proxmox(
        host=f"{os.getenv('ProxHost')}",
        user=f"{os.getenv('ProxUserPAM')}",
        password=f"{os.getenv('ProxPasswordPAM')}",
    )

@router.get(path="/get_vm_ids")
def get_vm_ids(node : str) -> Any:
    return call_proxmox().get_vm_ids(node=node)

@router.get(path="/get_next_available_vm_id")
def get_next_available_vm_id() -> Any:
    return {
        "vmid": int(call_proxmox().get_next_available_vm_id())
    }

@router.post(path="/create-vm/")
def create_vm(node: str, vm_config: VirtualMachine):
    try:
        config = vm_config.config
        vm = call_proxmox().create_vm(node=node,config=config)
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
        vm = call_proxmox().create_vm_pre_config(node=node,sshkeys=sshkeys,config=vm_config.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating VM: {e}")
    return vm

@router.post(path="/bash_command")
def execute_command(node : str, vmid : int, command : BashCommand):

    response = call_proxmox().bash_command(node=node, vmid=vmid, command=command.command)

    return response

@router.get(path="/get_network_setting_vm")
def get_network_setting_vm(node : str, vmid : int):

    response = call_proxmox().get_network_setting_vm(node=node, vmid=vmid)

    return response

@router.get(path="/get_vm_ipv4")
def get_vm_ipv4(node : str, vmid : int):

    response = call_proxmox().get_vm_ipv4(node=node, vmid=vmid)
    if response == None:
        raise HTTPException(500, detail=f"Chould not resive ipv4, see API log for more info")
    return response

@router.post("/execute-commands")
async def execute_commands(node: str, vmid: int, file: UploadFile = File(...)):
    content = await file.read()
    commands = yaml.safe_load(stream=content)

    if "runcmd" not in commands:
        return {"error": "Invalid YAML format"}

    responses = []
    for command in commands["runcmd"]:
        response = call_proxmox().bash_command(node=node, vmid=vmid, command=command)
        responses.append(response)
    
    return {"responses": responses}

@router.get("/list_vms")
def list_vms(node:str) -> Any:
    return call_proxmox().list_vms(node=node)
    
@router.get("/list_all_vm_ids")
def list_all_vm_ids() -> Any:

    return call_proxmox().list_all_vm_ids()

@router.get("/get_vm_status")
def get_vm_status(node: str, vmid: str) -> Any:
    return call_proxmox().get_vm_status(node=node, vmid=vmid)

@router.get("/get_vm_config")
def get_vm_config(node: str, vmid: str) -> Any:
    return call_proxmox().get_vm_config(node=node, vmid=vmid)

@router.delete("/delete_vm")
def delete_vm(node: str, vmid: str) -> Any:
    return call_proxmox().delete_vm(node=node, vmid=vmid)

@router.post("/clone_vm")
def clone_vm(newid: str, node: str, vmid: str) -> Any:
    return call_proxmox().clone_vm(newid=newid, node=node, vmid=vmid)

@router.post("/start_vm")
def start_vm(node: str, vmid: str) -> Any:
    return call_proxmox().start_vm(node=node, vmid=vmid)

@router.post("/stop_vm")
def stop_vm(node: str, vmid: str) -> Any:
    return call_proxmox().stop_vm(node=node, vmid=vmid)

@router.post("/shutdown_vm")
def shutdown_vm(node: str, vmid: str) -> Any:
    return call_proxmox().shutdown_vm(node=node, vmid=vmid)

@router.post("/reset_vm")
def reset_vm(node: str, vmid: str) -> Any:
    return call_proxmox().reset_vm(node=node, vmid=vmid)

@router.post("/reboot_vm")
def reboot_vm(node: str, vmid: str) -> Any:
    return call_proxmox().reboot_vm(node=node, vmid=vmid)

@router.post("/suspend_vm")
def suspend_vm(node: str, vmid: str) -> Any:
    return call_proxmox().suspend_vm(node=node, vmid=vmid)

@router.post("/resume_vm")
def resume_vm(node: str, vmid: str) -> Any:
    return call_proxmox().resume_vm(node=node, vmid=vmid)