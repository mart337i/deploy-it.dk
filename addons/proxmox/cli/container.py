# OS
import os
from typing import Optional, List, Annotated

# Third party imports
import rich
from rich.console import Console
from rich.table import Table
import typer
from typing_extensions import Annotated
from yaml import safe_load

# Local imports
from addons.proxmox.models.proxmox import proxmox, TokenAuth
from addons.proxmox.utils.yml_parser import read,validate

from clicx.config import configuration
from clicx.utils.jinja import render

console = Console()
app = typer.Typer(help="Setup and test tools for proxmomx")

def pve_conn(
    host: str = configuration.env['host'],
    user: str = configuration.env['user'],
    token_name: str = configuration.env["token_name"],
    token_value: str = configuration.env["token_value"],
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
    
@app.command(help="Install docker on a given Vm")
def install_docker(
    node,
    vmid
):

    commands_string = render("install_docker_engine.yml")
    yml_loaded_commands = safe_load(commands_string)
    responses = []
    for command in yml_loaded_commands['SetUpDocker-24.04'].get("commands"):
        try:
            response = pve_conn().execute_command(node=node, vmid=vmid, command=command)
            responses.append({
                "command": command,
                "status": "success",
                "response": response
            })
        except Exception as e:
            responses.append({
                "command": command,
                "status": "error",
                "error": str(e)
            })
    
    rich.print(responses)