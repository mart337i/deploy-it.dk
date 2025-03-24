# Standard library imports
import os
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Annotated, Dict, Optional, Any, List

# Third-party imports
import rich
import typer
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

# Local imports
from clicx.config import addons, templates_dir, configuration
from clicx.cli.server import API
from clicx.cli.server import cli as server_cli

cli = typer.Typer(help="Clicx CLI application")
cli.add_typer(server_cli)

def discover_commands(commands_dir: Path):
    """Discover and register commands from CLI directories"""
    if not commands_dir.exists():
        rich.print(f"[red]Command directory not found at {commands_dir}[/red]")
        return
    
    module_apps = {}
    
    for cli_dir in commands_dir.glob("**/cli"):
        if not cli_dir.is_dir():
            continue
        
        parent_module = cli_dir.parent.name
        
        if parent_module not in module_apps:
            module_apps[parent_module] = typer.Typer(name=parent_module, help=f"Commands for {parent_module}")
        
        for item in cli_dir.iterdir():
            if item.name == '__init__.py':
                continue
            
            if item.name.endswith('.py'):
                try:
                    parts = list(cli_dir.parts)
                    if "addons" in parts:
                        addons_index = parts.index("addons")
                        module_parts = parts[addons_index:]
                        module_name = item.name.replace('.py', '')
                        import_path = ".".join(module_parts + [module_name])
                    else:
                        module_name = item.name.replace('.py', '')
                        import_path = f"cli.{module_name}"  # Simple fallback
                    
                    module = import_module(import_path)
                    
                    if hasattr(module, 'app') and isinstance(module.app, typer.Typer):
                        cmd_name = getattr(module, 'name', module_name)
                        module_apps[parent_module].add_typer(module.app, name=cmd_name)
                        
                        if hasattr(module, '__doc__') and module.__doc__:
                            module.app.info.help = module.__doc__.strip()
                        
                        if configuration.debug:
                            rich.print(f"[green]Registered command: {parent_module} {cmd_name} from {import_path}[/green]")
                    else:
                        if configuration.debug:
                            rich.print(f"[yellow]Module {import_path} does not contain a typer app[/yellow]")
                    
                except ImportError as e:
                    if configuration.debug:
                        rich.print(f"[red]Failed to import module {import_path}: {e}[/red]")
                    continue
                except Exception as e:
                    if configuration.debug:
                        rich.print(f"[red]Error processing {cli_dir}/{item.name}: {e}[/red]")
                    continue
    
    # Add all module apps to the main CLI
    for module_name, module_app in module_apps.items():
        cli.add_typer(module_app)

@cli.command(help="Generate a config file with environment variables")
def generate(output_path: str = typer.Option("clicx.conf", help="Path to output the config file")):
    """Generate a configuration file with default environment variables."""
    configuration.create_config(output_path)


@cli.command(help="Show the current CLI version.")
def version():
    """Show the current version."""
    from clicx import VERSION
    rich.print(f"[bold]Version:[/bold] {VERSION}")

def main():
    """Main entry point for the CLI"""
    discover_commands(addons)
    cli()