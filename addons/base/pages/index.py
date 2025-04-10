from datetime import datetime

# Third-party imports
import rich
import typer
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter
from fastapi import Request


# Local imports
from clicx.utils.jinja import render
from clicx import NAME,VERSION

router = APIRouter(
    tags=["Root"],
)

dependency = []

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Root endpoint that renders the index.html template
    """
    # Prepare template context
    context = {
        "app_name": NAME,
        "title": "FastAPI Platform",
        "hero_title": f"Modern API Platform: {NAME.upper()}",
        "hero_subtitle": "Developer Documentation",
        "hero_description": "Explore our API endpoints and integrate with our services quickly and easily.",
        "github_url": "https://github.com/mart337i/deploy-it.dk",
        "endpoints": [route for route in request.app.routes],
        "extra_links": [],
        "current_year": datetime.now().year,
        "company_name": "Egeskov-olsen",
    }

    html_content = render("index.html.jinja", context=context)
    return HTMLResponse(content=html_content)