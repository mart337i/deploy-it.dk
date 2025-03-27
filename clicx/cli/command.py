# Standard library imports
from importlib import import_module
from pathlib import Path

# Third-party imports
import rich
import typer

# Local imports
from clicx.config import configuration
from clicx import addons
from clicx.cli.server import cli as server_cli

cli = typer.Typer(help="Clicx CLI application")
cli.add_typer(server_cli)

def discover_commands(commands_dir: Path):
    """Discover and register commands from CLI directories"""
    if not commands_dir.exists():
        rich.print(f"[red]Command directory not found at {commands_dir}[/red]")
        return
    
    module_apps = {}
    
    # Scan for CLI directories
    for cli_dir in commands_dir.glob("**/cli"):
        if not cli_dir.is_dir():
            continue
        
        parent_module = cli_dir.parent.name
        
        # Create a new Typer app for this module if it doesn't exist
        if parent_module not in module_apps:
            module_apps[parent_module] = typer.Typer(
                name=parent_module, 
                help=f"Commands for {parent_module}"
            )
        
        # Process Python files in the CLI directory
        for item in cli_dir.iterdir():
            if item.name == '__init__.py' or not item.name.endswith('.py'):
                continue
                
            try:
                # Determine the import path
                import_path = _build_import_path(cli_dir, item)
                module_name = item.name.replace('.py', '')
                
                # Import the module
                module = import_module(import_path)
                
                # Register the Typer app if available
                if hasattr(module, 'app') and isinstance(module.app, typer.Typer):
                    _register_typer_app(module, module_name, parent_module, module_apps, import_path)
                elif configuration.debug:
                    rich.print(f"[yellow]Module {import_path} does not contain a typer app[/yellow]")
                    
            except ImportError as e:
                _log_error(f"Failed to import module {import_path}", e)
            except Exception as e:
                _log_error(f"Error processing {cli_dir}/{item.name}", e)
    
    # Add all module apps to the main CLI
    for module_name, module_app in module_apps.items():
        cli.add_typer(module_app)


def _build_import_path(cli_dir: Path, item: Path) -> str:
    """Build the correct import path for a module."""
    parts = list(cli_dir.parts)
    module_name = item.name.replace('.py', '')
    
    if "addons" in parts:
        addons_index = parts.index("addons")
        module_parts = parts[addons_index:]
        return ".".join(module_parts + [module_name])
    else:
        return f"cli.{module_name}"


def _register_typer_app(module, module_name, parent_module, module_apps, import_path):
    """Register a Typer app with its parent module."""
    cmd_name = getattr(module, 'name', module_name)
    module_apps[parent_module].add_typer(module.app, name=cmd_name)
    
    # Add doc string as help if available
    if hasattr(module, '__doc__') and module.__doc__:
        module.app.info.help = module.__doc__.strip()
    
    if configuration.debug:
        rich.print(f"[green]Registered command: {parent_module} {cmd_name} from {import_path}[/green]")


def _log_error(message: str, error: Exception):
    """Log an error message if debug is enabled."""
    if configuration.debug:
        rich.print(f"[red]{message}: {error}[/red]")

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