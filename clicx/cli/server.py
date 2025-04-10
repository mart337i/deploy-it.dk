import typer
from typing import Optional, Annotated

cli = typer.Typer()

@cli.command(
    help="Start the application",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def server(
    ctx: typer.Context,
    host: Annotated[Optional[str], typer.Option(help='Bind socket to this host')] = "0.0.0.0",
    port: Annotated[Optional[int], typer.Option(help='Bind socket to this port')] = 8000,
    reload: Annotated[Optional[bool], typer.Option(help='Enable auto-reload')] = True,
    workers: Annotated[Optional[int], typer.Option(help='Number of worker processes')] = None,
):
    """Start the server application."""
    from clicx.server import create_api
    
    # Prepare configuration
    loaded_conf = {
        key: value 
        for key, value in locals().items() 
        if value is not None and key != "api"
    }
    
    # Now configure and start the app
    create_api().start(config=loaded_conf)