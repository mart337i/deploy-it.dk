from datetime import datetime
from typing import List

# Third-party imports
from fastapi.routing import APIRouter

# Local imports
from clicx.utils.jinja import _env

router = APIRouter(
    prefix=f"/utils/templates",
    tags=["Utils for templates"],
)

dependency = []

@router.get("/get_templates")
async def list_templates() -> dict[str, List[str]]:
    templates = _env.list_templates()
    return {
        "templates": templates,
    }