# software_routes.py
from fastapi import File, HTTPException, UploadFile, Depends
from fastapi.routing import APIRouter
from proxmox.service.proxmox import Proxmox
from proxmox import API_VERSION, NAME
from proxmox.service import proxmox

def get_pve_conn() -> Proxmox:
    return proxmox.get_connection()

router = APIRouter(
    prefix=f"/{NAME}/{API_VERSION}/software",
    tags=["Software Management"],
)

dependency = []

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
    port: int,
    vmid: int = 3000,
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        return pve.software.create_proxy_conf(node=node, vmid=vmid, hostname=hostname, ip=ip, port=port)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create proxy configuration: {str(e)}")

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