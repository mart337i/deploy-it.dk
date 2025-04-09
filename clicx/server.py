# Standard library imports
import os
import importlib

# Third-party imports
from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import rich

# Local application imports
from clicx.config import configuration
from clicx.utils.middleware import log_request_info
from clicx import VERSION

import logging
_logger = logging.getLogger(__name__)

# Miscellaneous
import urllib3

# Disable SSL warnings
urllib3.disable_warnings()

class API(FastAPI):
    def __init__(
            self,
            title : str = "FastApi",
            openapi_url: str = "/openapi.json",
            docs_url : str = "/docs",
            description: str = "API",
            version: str = "0.1.0",
            license_info : dict = {
                "name": "Apache 2.0",
                "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
            },
            contact: dict = {
                "name": "Deadpoolio the Amazing",
                "url": "http://x-force.example.com/contact/",
                "email": "dp@x-force.example.com",
            },
        ):
        
        # Run Base class init
        super().__init__(
            title=title,
            openapi_url=openapi_url,
            docs_url=docs_url,
            description=description,
            version=version,
            license_info=license_info,
            contact=contact,
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
                dependencies = module.dependency.copy()
                dependencies.append(Depends(dependency=log_request_info))
                
                self.include_router(
                    router=module.router,
                    dependencies=dependencies
                )

                _logger.debug(f"Registered router from module: {module_name} and dependency {dependencies}")
        except ModuleNotFoundError as e:
            _logger.error(f"Module not found: {module_name}, error: {e}")
        except AttributeError as e:
            _logger.error(f"Module '{module_name}' does not have 'router' attribute, error: {e}")
        except Exception as e:
            _logger.error(f"Module '{module_name}' failed with the following error: {e}")

    def register_routes(self):
        """
            Loop a dir for all python files in addons/ dir, 
            and run include_router_from_module()
        """
        addons_dir = configuration.addons
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
            timeout_keep_alive=10,
            log_config=None,
            access_log=None
        )

# This is the name of the application, as seen in the server file.
# It is needed to be able to configure workers and set reload=true on uvicorn. 
# The name and api instance need to match for uvicorn's lifespan to work correctly
api : API = API(
    title="Deploy-it API",
    description= """
        This REST API, built with FastAPI and Proxmoxer, automates the creation of virtual machines on a Proxmox virtualization environment for Company X. It provides endpoints to deploy, configure, and manage VMs efficiently, streamlining the provisioning process while ensuring consistency and reliability.
    """,
    version=VERSION,
    license_info={
        'name': "MIT",
        'url' : "https://mit-license.org/"
    },
    contact={
        "name": "Deploy-it.dk",
        "url" : "https://www.Deploy-it.dk",
        "email" : "Info@deploy-it.dk"
    }
)