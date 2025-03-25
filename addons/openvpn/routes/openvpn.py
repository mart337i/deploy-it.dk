from datetime import datetime
from typing import List

# Third-party imports
from fastapi.routing import APIRouter

# Local imports
from clicx.utils.jinja import _env

router = APIRouter(
    prefix=f"/openvpn",
    tags=["Openvpn creation and configuration"],
)

dependency = []