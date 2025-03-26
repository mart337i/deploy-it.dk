# OS
import os
from typing import Optional, List

# Third party imports
import rich
from rich.console import Console
from rich.table import Table
import typer
from typing_extensions import Annotated

# Local imports
from addons.proxmox.models.proxmox import proxmox

console = Console()
app = typer.Typer(help="Proxmox VE management commands")


def pve_conn() -> proxmox:
    """
    Create a connection to proxmox via an api wrapper proxAPI, which then implements proxmoxer
    > pve_conn stands for "Proxmox Virtual Environment Connection".
    """
    return proxmox(
        host=f"{os.getenv('ProxHost')}",
        user=f"{os.getenv('ProxUserPAM')}",
        password=f"{os.getenv('ProxPasswordPAM')}",
    )


@app.command()
def create(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    name: str = typer.Option(..., "--name", help="VM name"),
    disk_size: str = typer.Option("10G", "--disk-size", "-d", help="Disk size (e.g., '10G')"),
    memory: int = typer.Option(1024, "--memory", "-m", help="Memory in MB"),
    cores: int = typer.Option(1, "--cores", "-c", help="Number of CPU cores"),
    sshkeys: str = typer.Option(None, "--sshkeys", help="SSH public keys (comma-separated or path to file)"),
    password: str = typer.Option(None, "--password", help="VM password (if not specified, will be generated)"),
    storage: str = typer.Option("local-lvm", "--storage", help="Storage location"),
    ostype: str = typer.Option("l26", "--ostype", help="OS type"),
):
    """Create a new virtual machine."""
    config = {
        'name': name,
        'cores': cores,
        'memory': memory,
        'ostype': ostype,
        'scsi0': f"{storage}:0,size={disk_size}",
        'disk_size': disk_size,
    }
    
    if password:
        config['cipassword'] = password
        
    # Load SSH keys from file if path is provided
    if sshkeys and os.path.isfile(sshkeys):
        with open(sshkeys, "r") as f:
            sshkeys = f.read().strip()
    
    # Call the existing method
    result = pve_conn().create_vm_pre_config(node=node, sshkeys=sshkeys, config={'config': config})
    console.print(f"[bold green]VM created successfully![/bold green]")
    console.print(f"VM ID: {result['vm']['id']}")
    console.print(f"Task ID: {result['task']['taskID']}")


@app.command()
def list_vms(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
):
    """List all VMs on a node."""
    vms = pve_conn().list_vms(node=node)
    
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
    result = pve_conn().start_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} start initiated. Task ID: {result}[/bold green]")


@app.command()
def stop(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Stop a VM."""
    result = pve_conn().stop_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} stop initiated. Task ID: {result}[/bold green]")


@app.command()
def shutdown(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Shutdown a VM (graceful)."""
    result = pve_conn().shutdown_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} shutdown initiated. Task ID: {result}[/bold green]")


@app.command()
def reset(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Reset a VM."""
    result = pve_conn().reset_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} reset initiated. Task ID: {result}[/bold green]")


@app.command()
def reboot(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Reboot a VM (graceful)."""
    result = pve_conn().reboot_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} reboot initiated. Task ID: {result}[/bold green]")


@app.command()
def status(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Get VM status."""
    result = pve_conn().get_vm_status(node=node, vmid=vmid)
    
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
    
    result = pve_conn().delete_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} deletion initiated. Task ID: {result}[/bold green]")


@app.command()
def list_nodes():
    """List all nodes in the cluster."""
    nodes = pve_conn().list_nodes()
    
    table = Table(title="Proxmox VE Nodes")
    
    table.add_column("Node")
    table.add_column("Status")
    table.add_column("CPU")
    table.add_column("Memory")
    table.add_column("Uptime")
    
    for node in nodes:
        table.add_row(
            node.get('node', ''),
            node.get('status', ''),
            f"{node.get('cpu', 0):.2f}%",
            f"{node.get('mem', 0) / (1024*1024*1024):.1f} GB",
            f"{node.get('uptime', 0) // 86400} days"
        )
    
    console.print(table)


@app.command()
def get_ip(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Get VM IP address."""
    result = pve_conn().get_vm_ipv4(node=node, vmid=vmid)
    
    if result:
        console.print(f"[bold green]VM {vmid} IP: {result.get('ipv4', 'Not available')}[/bold green]")
    else:
        console.print(f"[bold yellow]Could not retrieve IP for VM {vmid}[/bold yellow]")


@app.command()
def clone(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="Source VM ID"),
    newid: str = typer.Option(..., "--newid", help="New VM ID"),
    name: str = typer.Option(None, "--name", help="New VM name"),
    full: bool = typer.Option(False, "--full", help="Create a full clone"),
):
    """Clone a VM."""
    params = {}
    if name:
        params['name'] = name
    if full:
        params['full'] = 1
    
    result = pve_conn().clone_vm(node=node, vmid=vmid, newid=newid, **params)
    console.print(f"[bold green]VM {vmid} clone initiated. New VM ID: {newid}. Task ID: {result}[/bold green]")


@app.command()
def resize_disk(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
    disk: str = typer.Option("scsi0", "--disk", help="Disk to resize"),
    size: str = typer.Option(..., "--size", help="New disk size (e.g., '20G')"),
):
    """Resize a VM disk."""
    result = pve_conn().resize_vm_disk(node=node, vm_id=vmid, disk=disk, new_size=size)
    console.print(f"[bold green]VM {vmid} disk resize initiated. Task ID: {result.get('vm', {}).get('taskID', '')}[/bold green]")


@app.command()
def list_tasks(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    limit: int = typer.Option(10, "--limit", "-l", help="Limit number of tasks"),
):
    """List recent tasks on a node."""
    tasks = pve_conn().list_tasks(node=node, limit=limit)
    
    table = Table(title=f"Recent tasks on node {node}")
    
    table.add_column("Task ID")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Start Time")
    table.add_column("End Time")
    
    for task in tasks:
        table.add_row(
            task.get('upid', ''),
            task.get('type', ''),
            task.get('status', ''),
            task.get('starttime', ''),
            task.get('endtime', '')
        )
    
    console.print(table)


@app.command()
def task_status(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    upid: str = typer.Option(..., "--upid", "-u", help="Task ID"),
):
    """Get task status."""
    status = pve_conn().get_task_status(node=node, upid=upid)
    
    table = Table(title=f"Task {upid} Status")
    
    table.add_column("Property")
    table.add_column("Value")
    
    for key, value in status.items():
        table.add_row(key, str(value))
    
    console.print(table)


@app.command()
def task_logs(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    upid: str = typer.Option(..., "--upid", "-u", help="Task ID"),
):
    """Get task logs."""
    logs = pve_conn().get_task_logs(node=node, upid=upid)
    
    for log in logs:
        console.print(log.get('t', ''))


@app.command()
def suspend(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Suspend a VM."""
    result = pve_conn().suspend_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} suspend initiated. Task ID: {result}[/bold green]")


@app.command()
def resume(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Resume a suspended VM."""
    result = pve_conn().resume_vm(node=node, vmid=vmid)
    console.print(f"[bold green]VM {vmid} resume initiated. Task ID: {result}[/bold green]")


@app.command()
def config(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Get VM configuration."""
    config = pve_conn().get_vm_config(node=node, vmid=vmid)
    
    table = Table(title=f"Configuration of VM {vmid}")
    
    table.add_column("Property")
    table.add_column("Value")
    
    for key, value in config.items():
        table.add_row(key, str(value))
    
    console.print(table)


@app.command()
def version():
    """Get Proxmox VE version."""
    version = pve_conn().get_version()
    
    table = Table(title="Proxmox VE Version")
    table.add_column("Property")
    table.add_column("Value")
    
    for key, value in version.items():
        table.add_row(key, str(value))
    
    console.print(table)


@app.command()
def list_users():
    """List all users."""
    users = pve_conn().list_users()
    
    table = Table(title="Proxmox VE Users")
    table.add_column("User ID")
    table.add_column("Email")
    table.add_column("Enabled")
    table.add_column("Expiration")
    
    for user in users:
        table.add_row(
            user.get('userid', ''),
            user.get('email', ''),
            str(user.get('enable', True)),
            user.get('expire', 'Never')
        )
    
    console.print(table)


@app.command()
def list_roles():
    """List all roles."""
    roles = pve_conn().list_roles()
    
    table = Table(title="Proxmox VE Roles")
    table.add_column("Role")
    table.add_column("Privileges")
    
    for role in roles:
        table.add_row(
            role.get('roleid', ''),
            ", ".join(role.get('privs', []))
        )
    
    console.print(table)


@app.command()
def list_permissions():
    """List all permissions."""
    permissions = pve_conn().list_permissions()
    
    table = Table(title="Proxmox VE Permissions")
    table.add_column("Permission")
    table.add_column("Description")
    
    for perm in permissions:
        table.add_row(
            perm.get('path', ''),
            perm.get('description', '')
        )
    
    console.print(table)


@app.command()
def list_resources():
    """List all resources."""
    resources = pve_conn().list_resources()
    
    table = Table(title="Proxmox VE Resources")
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Status")
    
    for res in resources:
        table.add_row(
            res.get('id', ''),
            res.get('type', ''),
            res.get('name', ''),
            res.get('status', '')
        )
    
    console.print(table)


@app.command()
def get_next_vmid():
    """Get next available VM ID."""
    next_id = pve_conn().get_next_available_vm_id()
    console.print(f"[bold green]Next available VM ID: {next_id}[/bold green]")


@app.command()
def execute_vm_command(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
    command: str = typer.Option(..., "--command", "-c", help="Command to execute"),
):
    """Execute a command on a VM using QEMU agent."""
    result = pve_conn().execute_command(node=node, vmid=vmid, command=command)
    console.print(f"[bold blue]Command execution result:[/bold blue]")
    console.print(result)


@app.command()
def network_info(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
    vmid: str = typer.Option(..., "--vmid", "-v", help="VM ID"),
):
    """Get network settings for a VM."""
    network = pve_conn().get_network_setting_vm(node=node, vmid=vmid)
    
    table = Table(title=f"Network settings for VM {vmid}")
    table.add_column("Interface")
    table.add_column("MAC")
    table.add_column("IP Address")
    table.add_column("Type")
    
    for interface in network.get('result', []):
        for ip in interface.get('ip-addresses', []):
            table.add_row(
                interface.get('name', ''),
                interface.get('hardware-address', ''),
                ip.get('ip-address', ''),
                ip.get('ip-address-type', '')
            )
    
    console.print(table)


@app.command()
def node_network(
    node: str = typer.Option(..., "--node", "-n", help="Node name"),
):
    """Get network configuration for a node."""
    network = pve_conn().get_node_network_config(node=node)
    
    table = Table(title=f"Network configuration for node {node}")
    table.add_column("Interface")
    table.add_column("Type")
    table.add_column("Address")
    table.add_column("Active")
    
    for iface in network:
        table.add_row(
            iface.get('iface', ''),
            iface.get('type', ''),
            iface.get('address', ''),
            str(iface.get('active', False))
        )
    
    console.print(table)


@app.command()
def hostname_map():
    """Map hostnames to IP addresses for all nodes."""
    mapping = pve_conn().map_hostname_and_ip()
    
    table = Table(title="Node Hostname to IP Mapping")
    table.add_column("Hostname")
    table.add_column("IP Address")
    
    for item in mapping:
        table.add_row(
            item.get('hostname', ''),
            item.get('ip_address', '')
        )
    
    console.print(table)