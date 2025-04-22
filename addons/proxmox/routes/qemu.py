# qemu_routes.py
from fastapi import HTTPException, Depends
from fastapi.routing import APIRouter
from proxmox.service.proxmox import Proxmox
from proxmox import API_VERSION, NAME
from proxmox.service import proxmox

def get_pve_conn() -> Proxmox:
    return proxmox.get_connection()

router = APIRouter(
    prefix=f"/{NAME}/{API_VERSION}/qemu",
    tags=["QEMU Management"],
)

dependency = []


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