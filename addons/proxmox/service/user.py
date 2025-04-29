import logging
from typing import Any, Dict, List

_logger = logging.getLogger(__name__)

class UserManagement():

    def __init__(self, connection):
        self._proxmoxer  = connection

#######################
# MARK: User and Access Management
#######################
    def list_users(self, **kwargs) -> List[Dict[str, Any]]:
        """List all users."""
        return self._proxmoxer.access.users.get(**kwargs)

    def get_user(self, userid: str, **kwargs) -> Dict[str, Any]:
        """Get user details."""
        return self._proxmoxer.access.users(userid).get(**kwargs)

    def create_user(self, userid: str, password: str, **kwargs) -> Dict[str, Any]:
        """Create a user."""
        return self._proxmoxer.access.users.post(userid=userid, password=password, **kwargs)

    def delete_user(self, userid: str, **kwargs) -> Dict[str, Any]:
        """Delete a user."""
        return self._proxmoxer.access.users(userid).delete(**kwargs)

    def list_roles(self, **kwargs) -> List[Dict[str, Any]]:
        """List all roles."""
        return self._proxmoxer.access.roles.get(**kwargs)

    def list_permissions(self, **kwargs) -> List[Dict[str, Any]]:
        """List all permissions."""
        return self._proxmoxer.access.permissions.get(**kwargs)

    def get_access_control_list(self, **kwargs) -> List[Dict[str, Any]]:
        """Get access control list."""
        return self._proxmoxer.access.acl.get(**kwargs)

    def update_access_control_list(self, path: str, roles: str, **kwargs) -> Dict[str, Any]:
        """Update access control list."""
        return self._proxmoxer.access.acl.put(path=path, roles=roles, **kwargs)
