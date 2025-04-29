# vm_routes.py
from typing import Any
import validators
from fastapi import HTTPException, Depends
from fastapi.routing import APIRouter
from proxmox.service.proxmox import Proxmox
from proxmox.schema.vm import CloneVM, VirtualMachine
from proxmox.schema.task import Task
from proxmox import API_VERSION, NAME
from proxmox.service import proxmox

def get_pve_conn() -> Proxmox:
    return proxmox.get_connection()

router = APIRouter(
    prefix=f"/{NAME}/{API_VERSION}/vm",
    tags=["Virtual Machine Management"],
)
dependency = []

@router.get(path="/get_vm_ids")
def get_vm_ids(node: str, pve: Proxmox = Depends(get_pve_conn)) -> Any:
    try:
        return pve.vm.get_vm_ids(node=node)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get VM IDs: {str(e)}")

@router.get(path="/get_all_configurations")
def get_all_configurations(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    try:
        return pve.vm.get_all_configurations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configurations: {str(e)}")

@router.get(path="/get_next_available_vm_id")
def get_next_available_vm_id(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    try:
        return {
            "vmid": int(pve.vm.get_next_available_vm_id())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next available VM ID: {str(e)}")

@router.post(path="/clone_vm")
def clone_vm(
    node: str, 
    vm_config: CloneVM,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        if not validators.hostname(vm_config.name):
            raise HTTPException(422, "Invalid Hostname")
        return pve.vm.clone_vm(node=node, config=vm_config.model_dump())
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clone VM: {str(e)}")

@router.post(path="/create_vm")
def create_vm(
    node: str, 
    vm_config: VirtualMachine,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        config = vm_config.config
        vm = pve.vm.create_vm(node=node, config=config)
        return vm
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create VM: {str(e)}")

@router.put("/resize_disk")
def resize_disk(
    node: str,
    vmid: int,
    disk: str,
    new_size: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> None:
    try:
        return pve.vm.resize_disk(node=node, vmid=vmid, disk_name=disk, size=f'+{new_size}G')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resize disk: {str(e)}")

@router.get("/list_vms")
def list_vms(
    node: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    try:
        return pve.vm.list_vms(node=node)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list VMs: {str(e)}")

@router.get("/list_all_vm_ids")
def list_all_vm_ids(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    try:
        return pve.vm.list_all_vm_ids()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list all VM IDs: {str(e)}")

@router.get("/get_vm_status")
def get_vm_status(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    try:
        return pve.vm.get_vm_status(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get VM status: {str(e)}")

@router.get("/get_vm_config")
def get_vm_config(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    try:
        return pve.vm.get_vm_config(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get VM configuration: {str(e)}")

@router.delete("/delete_vm")
def delete_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Task:
    try:
        return pve.vm.delete_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete VM: {str(e)}")

@router.post("/start_vm")
def start_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Task:
    try:
        return pve.vm.start_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start VM: {str(e)}")

@router.post("/stop_vm")
def stop_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Task:
    try:
        return pve.vm.stop_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop VM: {str(e)}")

@router.post("/shutdown_vm")
def shutdown_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Task:
    try:
        return pve.vm.shutdown_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to shutdown VM: {str(e)}")

@router.post("/reset_vm")
def reset_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Task:
    try:
        return pve.vm.reset_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset VM: {str(e)}")

@router.post("/reboot_vm")
def reboot_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Task:
    try:
        return pve.vm.reboot_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reboot VM: {str(e)}")

@router.post("/suspend_vm")
def suspend_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Task:
    try:
        return pve.vm.suspend_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suspend VM: {str(e)}")

@router.post("/resume_vm")
def resume_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Task:
    try:
        return pve.vm.resume_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume VM: {str(e)}")