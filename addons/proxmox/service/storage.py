
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

    def get_disk_size(self, node, vmid, disk_name):
        try:
            config = self._proxmoxer.nodes(node).qemu(vmid).config.get()
            
            for key, value in config.items():
                if key == disk_name or (key.startswith(disk_name) and key[len(disk_name)].isdigit()):
                    if isinstance(value, str) and "size=" in value:
                        size_part = [part for part in value.split(',') if part.startswith('size=')]
                        if size_part:
                            return size_part[0].replace('size=', '')
                    elif isinstance(value, dict) and 'size' in value:
                        return value['size']
            
            return None
            
        except Exception as e:
            raise Exception(f"Failed to get disk size: {str(e)}")