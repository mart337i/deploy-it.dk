# Standard library imports
import os
import importlib
from datetime import datetime
from pathlib import Path
from typing import Annotated, Dict, Optional, Any, List

# Third-party imports
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import rich
import typer

# Local application imports
from clicx.config import addons, templates_dir, configuration
from clicx.utils.middleware import log_request_info
from clicx.utils.python import deep_merge
from clicx.database.cr import DatabaseManager
from clicx import VERSION

import logging
_logger = logging.getLogger("app")

# Miscellaneous
import urllib3

# Disable SSL warnings
urllib3.disable_warnings()

class API(FastAPI):
    def __init__(self):
        super().__init__(
            title="API",
            openapi_url=f"/openapi.json",
            docs_url="/docs/",
            description=f"API",
            version=VERSION,
            license_info={
                "name": "MIT",
                "url": "https://pitt.libguides.com/openlicensing/MIT",
            },
            contact={
                "name": "Deploy-it.dk",
                "url": "https://deploy-it.dk",
                "email": "dev@deploy-it.dk",
            }
        )
        
        # Setup the application
        self.setup_base_routes()
        self.setup_addon_routers()
        self.use_route_names_as_operation_ids()
        self.setup_middleware()

    def setup_base_routes(self) -> None:
        pass

    def setup_addon_routers(self) -> None:
        """
            Import all routes using dynamic importing (Reflections)
        """
        self.register_routes()

    def setup_middleware(self):
        origins = [
            "http://localhost",
            "http://localhost:8000",
            "http://localhost:8080",
        ]

        self.add_middleware(
            middleware_class=CORSMiddleware,
            allow_credentials=True,
            allow_origins=origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # NOTE:: Enable this if it need to be exposed to the WAN
        # self.add_middleware(
        #     # Ensures all trafic to server is ssl encrypted or is rederected to https / wss
        #     middleware_class=HTTPSRedirectMiddleware
        # )

    def use_route_names_as_operation_ids(self) -> None:
        """
        Simplify operation IDs so that generated API clients have simpler function
        names.

        Should be called only after all routes have been added.
        """
        route_names = set()
        route_prefix = set()
        for route in self.routes:
            if isinstance(route, APIRoute):
                if route.name in route_names:
                    raise Exception(f"Route function names {[route.name]} should be unique")
                if route.path in route_prefix:
                    raise Exception(f"Route prefix {[route.path]} should be unique")
                route.operation_id = route.name
                route_names.add(route.name)
                route_prefix.add(route.path)

    def include_router_from_module(self, module_name: str):
        """
        Import module and check if it contains 'router' attribute.
        if it does include the route in the fastapi app 
        """
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, 'router') and hasattr(module, 'dependency'):
                self.include_router(
                    router=module.router,
                    dependencies=module.dependency.append(
                        Depends(dependency=log_request_info),
                    )
                )
                rich.print(f"[green]Registered router from module: {module_name} and dependency {module.dependency}[/green]")
        except ModuleNotFoundError as e:
            rich.print(f"[red]Module not found: {module_name}, error: {e}[/red]")
        except AttributeError as e:
            rich.print(f"[red]Module '{module_name}' does not have 'router' attribute, error: {e}[/red]")
        except Exception as e:
            rich.print(f"[red]Module '{module_name}' failed with the following error: {e}[/red]")

    def register_routes(self):
        """
            Loop a dir for all python files in addons/ dir, 
            and run include_router_from_module()
        """
        addons_dir = configuration.commands_dir
        addons_dir_name = 'addons'

        for root, dirs, files in os.walk(addons_dir):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    relative_path = os.path.relpath(os.path.join(root, file), addons_dir)
                    module_name = os.path.join(addons_dir_name, relative_path).replace(os.sep, '.')[:-3]
                    self.include_router_from_module(module_name=module_name)

    def start(self, config : dict):
        uvicorn.run(
            app=f"clicx.cli.server:api",
            lifespan="on",
            host=config.get("host"),
            port=config.get("port"),
            reload=config.get("reload"),
        )


# This is the name of the application, as seen in the server file.
# It is needed to be able to configure workers and set reload=true on uvicorn. 
# The name and api instance need to match for uvicorn's lifespan to work correctly
api = API()
cli = typer.Typer(help="Clicx server application")


@cli.command(help="Start the application")
def server(
    config_file: Annotated[Optional[Path], typer.Option("--config", help='Server config file')] = None,
    host: Annotated[Optional[str], typer.Option(help='Bind socket to this host')] = "0.0.0.0",
    port: Annotated[Optional[int], typer.Option(help='Bind socket to this port')] = 8000,
    reload: Annotated[Optional[bool], typer.Option(help='Enable auto-reload')] = True,
    log_level: Annotated[Optional[str], typer.Option(help='Log level')] = None,
    workers: Annotated[Optional[int], typer.Option(help='Number of worker processes')] = None,
    database: Annotated[Optional[str], typer.Option(help="Database name")] = None,
    username: Annotated[Optional[str], typer.Option(help="Database username")] = None,
    database_password: Annotated[Optional[str], typer.Option(help="Database user password")] = None,
    init_database: Annotated[Optional[bool], typer.Option(help='Initialize database')] = False,
    update_database: Annotated[Optional[bool], typer.Option(help="Update database using migrations")] = False,
    save_config: Annotated[Optional[bool], typer.Option(default="--save",help="Generate config file")] = False,
):
    """Start the server application with optional database operations."""
    loaded_conf = {key: value for key, value in locals().items() if value is not None and key != "config_file"}
    
    if config_file:
        config_file_data = configuration.load_config(config_file=config_file)
        loaded_conf = deep_merge(dict1=config_file_data, dict2=loaded_conf)
    
    # Handle database operations before starting the server
    if init_database or update_database:
        db_manager = DatabaseManager(
            username=loaded_conf.get('username'),
            password=loaded_conf.get('database_password'),
            hostname=loaded_conf.get('hostname', 'localhost'),
            database_name=loaded_conf.get('database')
        )
        
        if init_database:
            typer.echo("Initializing database...")
            db_manager.init_database()
            typer.echo("Database initialized successfully!")
            
        if update_database:
            typer.echo("Updating database using migrations...")
            db_manager.update_database()
            typer.echo("Database updated successfully!")

    if save_config:
        default_config_path = ".config/clicx/clicx.conf"
        config_path : Path = Path(Path(__file__).parent.parent, default_config_path)
        if not os.path.exists(config_path):
            return
        # Create/edit config with the loaded config.
        Ellipsis

    # Start the API server
    api.start(config=loaded_conf)