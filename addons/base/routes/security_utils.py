from datetime import datetime

# Third-party imports
import rich
import typer
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter

# Local imports
from clicx.utils.jinja import render
from clicx.utils.security import _generate_password

router = APIRouter(
    prefix=f"/utils/security",
    tags=["Utils for security"],
)

dependency = []

@router.get("/", response_class=HTMLResponse)
async def generate_password(len : int) -> str:
    return _generate_password(len)