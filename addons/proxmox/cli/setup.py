# OS
import os
from typing import Optional, List, Annotated

# Third party imports
import rich
from rich.console import Console
from rich.table import Table
import typer
from typing_extensions import Annotated

# Local imports
from addons.proxmox.models.proxmox import proxmox, TokenAuth
from clicx.config import configuration

console = Console()
app = typer.Typer(help="Setup and test tools for proxmomx")

def pve_conn(
    host: str = configuration.loaded_config['host'],
    user: str = configuration.loaded_config['user'],
    token_name: str = configuration.loaded_config["token_name"],
    token_value: str = configuration.loaded_config["token_value"],
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
    

@app.command(help="Test token auth to the proxmox instance")
def test_token2(
    host: Annotated[str, typer.Option(help="hostname")] = configuration.loaded_config['host'],
    user: Annotated[str, typer.Option(help="user")] = configuration.loaded_config['user'],
    token_name: Annotated[str, typer.Option(help="token name")] = configuration.loaded_config["token_name"],
    token_value: Annotated[str, typer.Option(help="token value")] = configuration.loaded_config["token_value"],
    verify_ssl: Annotated[bool, typer.Option(help="verify ssl")] = False,
    auth_type: Annotated[str, typer.Option(help="auth type")] = "token",
):

    result = pve_conn(
        **vars(TokenAuth(
            host=host,
            user=user,
            token_name=token_name,
            token_value=token_value,
            verify_ssl=verify_ssl,
            auth_type=auth_type,
        )
    )).get_version()

    rich.print(result)


@app.command(help="Test token auth to the proxmox instance")
def test_token(

):

    result = pve_conn().get_version()

    rich.print(result)
