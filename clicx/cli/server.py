# Standard library imports
from typing import Annotated, Optional

# Third-party imports
import typer

# Local application imports
from clicx.server import API

import logging
_logger = logging.getLogger("app")

# This is the name of the application, as seen in the server file.
# It is needed to be able to configure workers and set reload=true on uvicorn. 
# The name and api instance need to match for uvicorn's lifespan to work correctly
api = API()
cli = typer.Typer(help="Clicx server application")


@cli.command(help="Start the application")
def server(
    host: Annotated[Optional[str], typer.Option(help='Bind socket to this host')] = "0.0.0.0",
    port: Annotated[Optional[int], typer.Option(help='Bind socket to this port')] = 8000,
    reload: Annotated[Optional[bool], typer.Option(help='Enable auto-reload')] = True,
    log_level: Annotated[Optional[str], typer.Option(help='Log level')] = None,
    workers: Annotated[Optional[int], typer.Option(help='Number of worker processes')] = None,
):
    """Start the server application with optional database operations."""
    loaded_conf = {key: value for key, value in locals().items() if value is not None and key}

    api.start(config=loaded_conf)