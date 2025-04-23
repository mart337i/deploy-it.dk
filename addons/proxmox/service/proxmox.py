from typing import Dict, Any, List
from proxmoxer import ProxmoxAPI

from proxmox.enums.auth import Authtype
from proxmox.enums.proxmox import BackendType
from clicx.utils.exceptions import SleepyDeveloperError
from clicx.config import configuration

# Import managers
from proxmox.service.cluster import ClusterManagement
from proxmox.service.networking import NetworkManagment
from proxmox.service.qemu import QemuAgentManagement
from proxmox.service.software import SoftwareMangement
from proxmox.service.storage import StorageManagement
from proxmox.service.task import TaskManagement
from proxmox.service.vm import VirtualMachineManagement
from proxmox.service.user import UserManagement

from proxmox.utils.exceptions import InvalidConfiguration

class Proxmox:
    """Main client for interacting with Proxmox VE via the proxmoxer API."""
    
    def __init__(
        self,
        host: str,
        auth_type: Authtype,
        user: str,
        token_name=False,
        token_value=False,
        password=False,
        backend: BackendType="https",
        verify_ssl=False
    ):
        """
        Initialize the Proxmox client.
        
        Args:
            host: Hostname or IP address of the Proxmox server
            auth_type: Type of authentication (token or password)
            user: Username for authentication
            token_name: Token name for token authentication
            token_value: Token value for token authentication
            password: Password for password authentication
            backend: Backend type for the API connection
            verify_ssl: Whether to verify SSL certificates
        """

        if auth_type == Authtype.token:
            self._proxmoxer = ProxmoxAPI(
                host=host,
                backend = backend,
                user=user,
                token_name = token_name,
                token_value=token_value,
                verify_ssl=verify_ssl,
                timeout=30,
            )
        elif auth_type == Authtype.password:
            self._proxmoxer = ProxmoxAPI(
                host=host,
                backend = backend,
                user = user,
                password=password,
                verify_ssl=verify_ssl,
                timeout=30,
            )
        else: 
            raise SleepyDeveloperError("missing auth type")

        
        self._host = host
        self.available_nodes = list(configuration.loaded_config.get("available_nodes"))
        
        self.vm = VirtualMachineManagement(self._proxmoxer)
        self.network = NetworkManagment(self._proxmoxer)
        self.task = TaskManagement(self._proxmoxer)
        self.qemu = QemuAgentManagement(self._proxmoxer)
        self.cluster = ClusterManagement(self._proxmoxer)
        self.storage = StorageManagement(self._proxmoxer)
        self.user = UserManagement(self._proxmoxer)
        
        # NOTE inherits from QemuAgentManagement
        self.software = SoftwareMangement(self._proxmoxer)
    
    @property
    def host(self) -> str:
        """Get the host address."""
        return self._host
    
    @property
    def proxmoxer(self) -> ProxmoxAPI:
        """Get the proxmoxer API instance."""
        return self._proxmoxer
    
    def get_version(self, **kwargs) -> Dict[str, Any]:
        """Get Proxmox VE version."""
        return self._proxmoxer.version.get(**kwargs)
    
def get_connection() -> Proxmox:
    try: 
        host = configuration.loaded_config['host']
        user = configuration.loaded_config['user']
        token_name = configuration.loaded_config["token_name"]
        token_value = configuration.env.get('token_value',False)
        verify_ssl = False
        auth_type = Authtype.token

        if not token_value:
            raise InvalidConfiguration("Missing token in loaded env.")
        
    except Exception as e:
        raise SleepyDeveloperError(f"Missing required configuration key: {e}")

    return Proxmox(
        host=host,
        auth_type=auth_type,
        user=user,
        token_name=token_name,
        token_value=token_value,
        verify_ssl=verify_ssl
    )
