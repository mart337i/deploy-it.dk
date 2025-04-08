from datetime import datetime

# Third-party imports
import rich
import typer
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter

# Local imports
from clicx.config import configuration

router = APIRouter(
    prefix=f"/utils/config",
    tags=["Utils for config"],
)

dependency = []

@router.get("/get_config", response_class=HTMLResponse)
async def get_config() -> str:
    return {"ok": configuration.loaded_config}

@router.get("/get_env", response_class=HTMLResponse)
async def get_env() -> str:
    return {"ok": configuration.env}