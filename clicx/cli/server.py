# Standard library imports
from typing import Annotated, Optional

# Third-party imports
import typer

# Local application imports
from clicx.server import api

import logging
_logger = logging.getLogger("app")

cli = typer.Typer(help="Clicx server application")


@cli.command(help="Start the application")
def server(
    host: Annotated[Optional[str], typer.Option(help='Bind socket to this host')] = "0.0.0.0",
    port: Annotated[Optional[int], typer.Option(help='Bind socket to this port')] = 8000,
    reload: Annotated[Optional[bool], typer.Option(help='Enable auto-reload')] = True,
    workers: Annotated[Optional[int], typer.Option(help='Number of worker processes')] = None,
):
    """Start the server application."""
    loaded_conf = {key: value for key, value in locals().items() if value is not None and key}
    api.start(config=loaded_conf)