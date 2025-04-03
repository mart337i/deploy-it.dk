# OS
import os
from typing import Annotated, List, Optional

# Third party imports
import rich
import typer
from proxmox.models.auth import TokenAuth
# Local imports
from proxmox.models.proxmox import proxmox
from proxmox.utils.yml_parser import read, validate
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from yaml import safe_load

from clicx.config import configuration
from clicx.utils.jinja import render

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
    