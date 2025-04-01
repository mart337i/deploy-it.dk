
# Third-party imports
from fastapi.routing import APIRouter

from fastapi.routing import APIRouter
from typing import Any


from addons.proxmox.models.proxmox import proxmox, TokenAuth

from clicx.config import configuration

router = APIRouter(
    prefix=f"/proxmox/v1/node",
    tags=["Proxmox nodes"],
)

dependency = []

def pve_conn(
    host: str = configuration.loaded_config['host'],
    user: str = configuration.loaded_config['user'],
    token_name: str = configuration.loaded_config["token_name"],
    token_value: str = configuration.loaded_config["token_value"],
    verify_ssl: bool = False,
    auth_type: str = "token",
):
    return proxmox(
        **vars(TokenAuth(
            host=host,
            user=user,
            token_name=token_name,
            token_value=token_value,
            verify_ssl=verify_ssl,
            auth_type=auth_type,
        ))
    )


@router.get("/")
def Proxmox_Root() -> Any:
    return {
        "get_version" : f"{pve_conn().get_version()}",
    }

@router.get("/list_all_nodes")
def list_all_nodes() -> Any:
    nodes = []

    temp_connection = pve_conn()
    for node in temp_connection.list_nodes():
        node_name = node.get("node")
        nodes.append(node_name)
        
    return nodes

@router.get("/list_nodes")
def list_nodes() -> Any:
    return  pve_conn().list_nodes()
    

@router.get("/get_node_status")
def get_node_status(node: str) -> Any:
    return {
        "node_status": f"{pve_conn().get_node_status(node=node)}",
    }

@router.get("/list_resources")
def list_resources() -> Any:
    return {
        "resources": f"{pve_conn().list_resources()}",
    }