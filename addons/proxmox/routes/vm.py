from typing import Annotated, Any

import validators
from fastapi import File, HTTPException, UploadFile, Depends
from fastapi.routing import APIRouter
from proxmox.models.auth import TokenAuth
from proxmox.service.proxmox import Proxmox
from proxmox.service import proxmox
from proxmox.schema.vm import CloneVM, VirtualMachine

from clicx.config import configuration
from proxmox.middleware.auth import pass_through_authentication

from proxmox import API_VERSION,NAME

router = APIRouter(
    prefix=f"/{NAME}/{API_VERSION}/vm",
    tags=["Virtual machine control"],
)

dependency = [Depends(dependency=pass_through_authentication)]

def get_pve_conn() -> Proxmox:
    return proxmox.get_connection()

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

@router.post(path="/install_docker_engine")
def install_docker_engine(node: str, vmid: int, pve: Proxmox = Depends(get_pve_conn)):
    try:
        return pve.software.install_docker_engine(node, vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to install Docker engine: {str(e)}")

@router.post(path="/pull_docker_image")
def pull_docker_image(
    node: str, 
    vmid: int, 
    image_name: str, 
    container_name: str,
    port_mapping: str = "", 
    volume_mapping: str = "", 
    env_vars: str = "",
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.software.pull_docker_image(
            node=node,
            vmid=vmid,
            image_name=image_name,
            container_name=container_name,
            port_mapping=port_mapping,
            volume_mapping=volume_mapping,
            env_vars=env_vars
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pull Docker image: {str(e)}")

@router.post(path="/stop_docker_image")
def stop_docker_image(
    node: str, 
    vmid: int, 
    container_name: str, 
    remove_container: bool,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.software.stop_docker_image(node, vmid, container_name, remove_container)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop Docker container: {str(e)}")

@router.post(path="/create_proxy_conf")
def create_proxy_conf(
    node: str, 
    hostname: str, 
    ip: str, 
    vmid: int = 3000,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.software.create_proxy_conf(node, vmid, hostname, ip)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create proxy configuration: {str(e)}")

@router.get(path="/get_next_available_vm_id")
def get_next_available_vm_id(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    try:
        return {
            "vmid": int(pve.vm.get_next_available_vm_id())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next available VM ID: {str(e)}")

@router.post(path="/configure_vm")
def configure_vm(
    node: str, 
    vmid: int, 
    config_name: str,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.software.configure_vm(node=node, vmid=vmid, script_name=config_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure VM: {str(e)}")

@router.post(path="/configure_vm_custom")
def configure_vm_custom(
    node: str, 
    vmid: int, 
    config_file: UploadFile = File(...),
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.software.configure_vm_custom(node=node, vmid=vmid, script_file=config_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure VM with custom file: {str(e)}")

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

@router.get(path="/get_vm_ip")
def get_vm_ip(
    node: str, 
    vmid: int,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        response = pve.network.get_vm_ip(node=node, vmid=vmid)
        if response is None:
            raise HTTPException(500, detail="Could not receive IP, see API log for more info")
        return response
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get VM IP: {str(e)}")

@router.get(path="/ping_qemu")
def ping_qemu(
    node: str, 
    vmid: int,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        response = pve.qemu.ping_qemu(node=node, vmid=vmid)
        if response is None:
            raise HTTPException(500, detail="Failed to ping QEMU guest agent")
        return response
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ping QEMU agent: {str(e)}")

@router.get(path="/get_qemu_agent_status")
def get_qemu_agent_status(
    node: str, 
    vmid: int,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.qemu.get_qemu_agent_status(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QEMU agent status: {str(e)}")

@router.put("/resize_disk")
def resize_disk(
    node: str,
    vmid: int,
    disk: str,
    new_size: str,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.vm.resize_disk(node=node, vmid=vmid, disk_name=disk, size=f'+{new_size}G')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resize disk: {str(e)}")

@router.get("/get_task_status")
def get_task_status(
    node: str, 
    upid: str,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.task.get_task_status(node=node, upid=upid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.get("/list_tasks")
def list_tasks(
    node: str,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.task.list_tasks(node=node)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")

@router.get("/get_task_logs")
def get_task_logs(
    node: str, 
    upid: str,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.task.get_task_logs(node=node, upid=upid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task logs: {str(e)}")

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
) -> Any:
    try:
        return pve.vm.delete_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete VM: {str(e)}")

@router.post("/start_vm")
def start_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    try:
        return pve.vm.start_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start VM: {str(e)}")

@router.post("/stop_vm")
def stop_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    try:
        return pve.vm.stop_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop VM: {str(e)}")

@router.post("/shutdown_vm")
def shutdown_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    try:
        return pve.vm.shutdown_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to shutdown VM: {str(e)}")

@router.post("/reset_vm")
def reset_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    try:
        return pve.vm.reset_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset VM: {str(e)}")

@router.post("/reboot_vm")
def reboot_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    try:
        return pve.vm.reboot_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reboot VM: {str(e)}")

@router.post("/suspend_vm")
def suspend_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    try:
        return pve.vm.suspend_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suspend VM: {str(e)}")

@router.post("/resume_vm")
def resume_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    try:
        return pve.vm.resume_vm(node=node, vmid=vmid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume VM: {str(e)}")