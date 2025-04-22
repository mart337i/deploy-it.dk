# task_routes.py
from fastapi import HTTPException, Depends
from fastapi.routing import APIRouter
from proxmox.service.proxmox import Proxmox
from proxmox import API_VERSION, NAME
from proxmox.service import proxmox

def get_pve_conn() -> Proxmox:
    return proxmox.get_connection()

router = APIRouter(
    prefix=f"/{NAME}/{API_VERSION}/task",
    tags=["Task Management"],
)

dependency = []


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