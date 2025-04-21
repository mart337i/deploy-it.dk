# OS
import os
from typing import Optional, List
from pathlib import Path

# Third party imports
import rich
from rich.console import Console
from rich.table import Table
import typer
from typing_extensions import Annotated

# Local imports
from proxmox.service import proxmox
from proxmox.service.proxmox import Proxmox
from proxmox.models.auth import TokenAuth

from clicx.config import configuration

console = Console()
app = typer.Typer(help="Virtual machine management")


def get_pve_conn() -> Proxmox:
    return proxmox.get_connection()

@app.command()
def list_vms(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
):
    """List all VMs on a node."""
    vms = get_pve_conn().vm.list_vms(node=node)
    
    table = Table(title=f"VMs on node {node}")
    
    if detailed:
        table.add_column("VM ID")
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Memory")
        table.add_column("CPU")
        table.add_column("Disk")
        
        for vm in vms:
            table.add_row(
                str(vm.get('vmid', '')),
                vm.get('name', ''),
                vm.get('status', ''),
                f"{vm.get('maxmem', 0) / (1024*1024):.1f} MB",
                f"{vm.get('maxcpu', 0)} cores",
                f"{vm.get('maxdisk', 0) / (1024*1024*1024):.1f} GB"
            )
    else:
        table.add_column("VM ID")
        table.add_column("Name")
        table.add_column("Status")
        
        for vm in vms:
            table.add_row(
                str(vm.get('vmid', '')),
                vm.get('name', ''),
                vm.get('status', '')
            )
    
    console.print(table)


@app.command()
def start(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Start a VM."""
    result = get_pve_conn().vm.start_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} start initiated. Task ID: {result}[/bold green]")


@app.command()
def stop(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Stop a VM."""
    result = get_pve_conn().vm.stop_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} stop initiated. Task ID: {result}[/bold green]")


@app.command()
def shutdown(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Shutdown a VM (graceful)."""
    result = get_pve_conn().vm.shutdown_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} shutdown initiated. Task ID: {result}[/bold green]")


@app.command()
def reset(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Reset a VM."""
    result = get_pve_conn().vm.reset_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} reset initiated. Task ID: {result}[/bold green]")


@app.command()
def reboot(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Reboot a VM (graceful)."""
    result = get_pve_conn().vm.reboot_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} reboot initiated. Task ID: {result}[/bold green]")


@app.command()
def status(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Get VM status."""
    result = get_pve_conn().vm.get_vm_status(node=node, vmid=vmid)
    
    table = Table(title=f"Status of VM {vmid}")
    
    table.add_column("Property")
    table.add_column("Value")
    
    for key, value in result.items():
        table.add_row(key, str(value))
    
    console.print(table)


@app.command()
def delete(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Confirm deletion without prompt"),
):
    """Delete a VM."""
    if not confirm:
        confirmed = typer.confirm(f"Are you sure you want to delete VM {vmid} on node {node}?")
        if not confirmed:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
    
    result = get_pve_conn().vm.delete_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} deletion initiated. Task ID: {result}[/bold green]")
