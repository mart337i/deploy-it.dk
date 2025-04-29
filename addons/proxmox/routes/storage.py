# qemu_routes.py
from fastapi import HTTPException, Depends
from fastapi.routing import APIRouter
from proxmox.service.proxmox import Proxmox
from proxmox import API_VERSION, NAME
from proxmox.service import proxmox

def get_pve_conn() -> Proxmox:
    return proxmox.get_connection()

router = APIRouter(
    prefix=f"/{NAME}/{API_VERSION}/storage",
    tags=["Storage Management"],
)

dependency = []


@router.get(path="/get_disk_size")
def get_disk_size(
    node: str, 
    vmid: int,
    disk_name: str = 'scsi0',
    pve: Proxmox = Depends(get_pve_conn)
):
    try:
        res = pve.storage.get_disk_size(node=node, vmid=vmid, disk_name=disk_name)
        return {
            "space" : int(res.lower().split('m', 1)[0]) / 1000
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage size: {str(e)}")
