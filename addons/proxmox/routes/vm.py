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

@router.get(path="/get_vm_ids", dependencies=dependency)
def get_vm_ids(node: str, pve: Proxmox = Depends(get_pve_conn)) -> Any:
    return pve.vm.get_vm_ids(node=node)

@router.get(path="/get_all_configurations", dependencies=dependency)
def get_all_configurations(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    return pve.vm.get_all_configurations()

@router.post(path="/install_docker_engine", dependencies=dependency)
def install_docker_engine(node: str, vmid: int, pve: Proxmox = Depends(get_pve_conn)):
    return pve.software.install_docker_engine(node, vmid)

@router.post(path="/pull_docker_image", dependencies=dependency)
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
    return pve.software.pull_docker_image(
        node=node,
        vmid=vmid,
        image_name=image_name,
        container_name=container_name,
        port_mapping=port_mapping,
        volume_mapping=volume_mapping,
        env_vars=env_vars
    )

@router.post(path="/stop_docker_image", dependencies=dependency)
def stop_docker_image(
    node: str, 
    vmid: int, 
    container_name: str, 
    remove_container: bool,
    pve: Proxmox = Depends(get_pve_conn)
):
    return pve.software.stop_docker_image(node, vmid, container_name, remove_container)

@router.post(path="/create_proxy_conf", dependencies=dependency)
def create_proxy_conf(
    node: str, 
    hostname: str, 
    ip: str, 
    vmid: int = 3000,
    pve: Proxmox = Depends(get_pve_conn)
):
    return pve.software.create_proxy_conf(node, vmid, hostname, ip)

@router.get(path="/get_next_available_vm_id", dependencies=dependency)
def get_next_available_vm_id(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    return {
        "vmid": int(pve.vm.get_next_available_vm_id())
    }

@router.post(path="/configure_vm", dependencies=dependency)
def configure_vm(
    node: str, 
    vmid: int, 
    config_name: str,
    pve: Proxmox = Depends(get_pve_conn)
):
    return pve.software.configure_vm(node=node, vmid=vmid, script_name=config_name)

@router.post(path="/configure_vm_custom", dependencies=dependency)
def configure_vm_custom(
    node: str, 
    vmid: int, 
    config_file: UploadFile = File(...),
    pve: Proxmox = Depends(get_pve_conn)
):
    return pve.software.configure_vm_custom(node=node, vmid=vmid, script_file=config_file)

@router.post(path="/clone-vm", dependencies=dependency)
def clone_vm(
    node: str, 
    vm_config: CloneVM,
    pve: Proxmox = Depends(get_pve_conn)
):
    if not validators.hostname(vm_config.name):
        raise HTTPException(422, "Invalid Hostname")
    try: 
        return pve.vm.clone_vm(node=node, config=vm_config.model_dump())
    except Exception as e:
        raise HTTPException(500, str(e))
    
@router.post(path="/create-vm", dependencies=dependency)
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get(path="/get_vm_ip", dependencies=dependency)
def get_vm_ip(
    node: str, 
    vmid: int,
    pve: Proxmox = Depends(get_pve_conn)
):
    response = pve.network.get_vm_ip(node=node, vmid=vmid)
    if response is None:
        raise HTTPException(500, detail="Could not receive IP, see API log for more info")
    return response

@router.get(path="/ping_qemu", dependencies=dependency)
def ping_qemu(
    node: str, 
    vmid: int,
    pve: Proxmox = Depends(get_pve_conn)
):
    response = pve.qemu.ping_qemu(node=node, vmid=vmid)
    if response is None:
        raise HTTPException(500, detail="Failed to ping QEMU guest agent")
    return response

@router.get(path="/get_qemu_agent_status", dependencies=dependency)
def get_qemu_agent_status(
    node: str, 
    vmid: int,
    pve: Proxmox = Depends(get_pve_conn)
):
    return pve.qemu.get_qemu_agent_status(node=node, vm_id=vmid)

@router.put("/resize_disk", dependencies=dependency)
def resize_disk(
    node: str,
    vm_id: int,
    disk: str,
    new_size: str,
    pve: Proxmox = Depends(get_pve_conn)
):
    return pve.vm.resize_disk(node=node, vm_id=vm_id, disk=disk, new_size=new_size)

@router.get("/get_task_status", dependencies=dependency)
def get_task_status(
    node: str, 
    upid: str,
    pve: Proxmox = Depends(get_pve_conn)
):
    return pve.task.get_task_status(node=node, upid=upid)

@router.get("/list_tasks", dependencies=dependency)
def list_tasks(
    node: str,
    pve: Proxmox = Depends(get_pve_conn)
):
    return pve.task.list_tasks(node=node)

@router.get("/get_task_logs", dependencies=dependency)
def get_task_logs(
    node: str, 
    upid: str,
    pve: Proxmox = Depends(get_pve_conn)
):
    return pve.task.get_task_logs(node=node, upid=upid)

@router.get("/list_vms", dependencies=dependency)
def list_vms(
    node: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.list_vms(node=node)
    
@router.get("/list_all_vm_ids", dependencies=dependency)
def list_all_vm_ids(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    return pve.vm.list_all_vm_ids()

@router.get("/get_vm_status", dependencies=dependency)
def get_vm_status(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.get_vm_status(node=node, vmid=vmid)

@router.get("/get_vm_config", dependencies=dependency)
def get_vm_config(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.get_vm_config(node=node, vmid=vmid)

@router.delete("/delete_vm", dependencies=dependency)
def delete_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.delete_vm(node=node, vmid=vmid)

@router.post("/start_vm", dependencies=dependency)
def start_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.start_vm(node=node, vmid=vmid)

@router.post("/stop_vm", dependencies=dependency)
def stop_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.stop_vm(node=node, vmid=vmid)

@router.post("/shutdown_vm", dependencies=dependency)
def shutdown_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.shutdown_vm(node=node, vmid=vmid)

@router.post("/reset_vm", dependencies=dependency)
def reset_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.reset_vm(node=node, vmid=vmid)

@router.post("/reboot_vm", dependencies=dependency)
def reboot_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.reboot_vm(node=node, vmid=vmid)

@router.post("/suspend_vm", dependencies=dependency)
def suspend_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.suspend_vm(node=node, vmid=vmid)

@router.post("/resume_vm", dependencies=dependency)
def resume_vm(
    node: str, 
    vmid: str,
    pve: Proxmox = Depends(get_pve_conn)
) -> Any:
    return pve.vm.resume_vm(node=node, vmid=vmid)