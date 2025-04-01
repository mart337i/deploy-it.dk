from pydantic import BaseModel, Field
from typing import Optional
from typing import Dict, Any, Optional, List


class VirtualMachine(BaseModel):
    config: Dict[str, Any] = Field(..., description="VM configuration parameters")

    class Config:
        extra='allow'
        json_schema_extra = {
            "example": {
                "config" : {
                "vmid": 100,
                "name": "test-vm",
                "cores": 4,
                "memory": 8192,
                "ostype": "l26",
                "ide2": "local:iso/ubuntu-24.04-desktop-amd64.iso,media=cdrom",
                "scsi0": "local:100/vm-100-disk-0.qcow2,iothread=1,size=32G",
                "net0": "virtio,bridge=vmbr0",
                "agent": 1,
                "ciuser": "",
                "cipassword": "",
                "cicustom": "user=local:/var/lib/vz/snippets/base_ubuntu.yml",
                }
            }
        }

class CloneVM(BaseModel):
    vmid: int = Field(..., description="The VMID of the source VM to clone.")
    newid: Optional[int] = Field(None, description="The new VMID to assign to the clone. If not provided, one will be generated.")
    name: str = Field(..., description="Name for the cloned VM.")
    ciuser: Optional[str] = Field(None, description="Cloud-Init username override.")
    sshkeys: Optional[str] = Field(None, description="SSH public keys override for Cloud-Init.")

    class Config:
        extra = 'forbid'
        json_schema_extra = {
            "example": {
                "vmid": 8000,
                "newid": 200,
                "name": "ubuntu-cloud",
                "ciuser": "sysadmin",
                "sshkeys": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIArQk8YlZR7RseAQH42utnPRqo10xANdDpruL+UcFiaZ mart337i@gmail.com",
            }
        }

