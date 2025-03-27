
# Third-party imports
from fastapi.routing import APIRouter

from fastapi.routing import APIRouter


from addons.proxmox.models.proxmox import proxmox, TokenAuth

from clicx.config import configuration


router = APIRouter(
    prefix=f"/proxmox/v1/container",
    tags=["Proxmox container"],
)

dependency = []

def pve_conn(
    host: str = configuration.env['host'],
    user: str = configuration.env['user'],
    token_name: str = configuration.env["token_name"],
    token_value: str = configuration.env["token_value"],
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


