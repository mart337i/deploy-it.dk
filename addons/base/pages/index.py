from datetime import datetime

# Third-party imports
import rich
import typer
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter

# Local imports
from clicx.utils.jinja import render

router = APIRouter(
    tags=["Root"],
)

dependency = []

@router.get("/", response_class=HTMLResponse)
async def root():
    """
    Root endpoint that renders the index.html template
    """
    # Prepare template context
    context = {
        "app_name": "Modern API Platform",
        "title": "FastAPI Platform",
        "hero_title": "Modern API Platform",
        "hero_subtitle": "Developer Documentation",
        "hero_description": "Explore our API endpoints and integrate with our services quickly and easily.",
        "github_url": "https://github.com/mart337i/production-ready-fastapi",
        "endpoints": [],
        "extra_links": [],
        "current_year": datetime.now().year,
        "company_name": "Egeskov-olsen",
    }

    html_content = render("index.html.jinja", context=context)
    return HTMLResponse(content=html_content)