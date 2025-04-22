from typing import Any
from fastapi import Depends
from fastapi.routing import APIRouter
from proxmox.models.auth import TokenAuth
from proxmox.middleware.auth import pass_through_authentication
from proxmox.service import proxmox
from proxmox.service.proxmox import Proxmox
from clicx.config import configuration

from proxmox import API_VERSION,NAME


router = APIRouter(
    prefix=f"/{NAME}/{API_VERSION}/node",
    tags=["Proxmox nodes"],
)

dependency = [Depends(dependency=pass_through_authentication)]

def get_pve_conn():
    return proxmox.get_connection()

@router.get("/")
def Proxmox_Root(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    return {
        "get_version": f"{pve.get_version()}",
    }

@router.get("/list_all_nodes")
def list_all_nodes(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    nodes = []
    for node in pve.cluster.list_nodes():
        node_name = node.get("node")
        nodes.append(node_name)
       
    return nodes

@router.get("/list_nodes")
def list_nodes(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    return pve.cluster.list_nodes()
   
@router.get("/get_node_status")
def get_node_status(node: str, pve: Proxmox = Depends(get_pve_conn)) -> Any:
    return {
        "node_status": f"{pve.cluster.get_node_status(node=node)}",
    }

@router.get("/list_resources")
def list_resources(pve: Proxmox = Depends(get_pve_conn)) -> Any:
    return {
        "resources": f"{pve.cluster.list_resources()}",
    }