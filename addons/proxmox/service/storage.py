from proxmox.service.proxmox import Proxmox
from proxmoxer import ProxmoxAPI

class StorageManagement():

    def __init__(self, connection) -> Proxmox:
        self._proxmoxer : ProxmoxAPI = connection


    def get_iso_files(self, node):
        all_isos = []
        
        iso_storages = self.get_iso_storage(node)
        
        for storage in iso_storages:
            storage_id = storage['storage']
            
            try:
                isos = self._proxmoxer.nodes(node).storage(storage_id).content.get(content='iso')
                
                for iso in isos:
                    iso['storage_name'] = storage_id
                
                all_isos.extend(isos)
            except Exception as e:
                print(f"Warning: Could not get ISOs from storage '{storage_id}': {str(e)}")
        
        return all_isos

    def get_storage(self, node, **kwargs):
        return self._proxmoxer.nodes(node).storage.get()
