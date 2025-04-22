# network_routes.py
from fastapi import HTTPException, Depends
from fastapi.routing import APIRouter
from proxmox.service.proxmox import Proxmox
from proxmox import API_VERSION, NAME
from proxmox.service import proxmox

def get_pve_conn() -> Proxmox:
    return proxmox.get_connection()

router = APIRouter(
    prefix=f"/{NAME}/{API_VERSION}/network",
    tags=["Network Management"],
)

dependency = []

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