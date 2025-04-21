
import logging

_logger = logging.getLogger(__name__)

class StorageManagement():

    def __init__(self, connection):
        self._proxmoxer  = connection

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
                _logger.warning(f"Could not get ISOs from storage '{storage_id}': {str(e)}")
        
        return all_isos
    def get_storage(self, node, **kwargs):
        return self._proxmoxer.nodes(node).storage.get()
    
    def get_iso_storage(self, node):
        storages = self._proxmoxer.nodes(node).storage.get()
        iso_storages = [
            storage for storage in storages 
            if 'content' in storage and 'iso' in storage['content'].split(',')
        ]
        
        return iso_storages
