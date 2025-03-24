from pydantic import BaseModel, Field, Extra
from typing import Literal
from typing import Optional
from typing import Dict, Any

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


class VirtualMachineCI(BaseModel):
    config: Dict[str, Any] = Field(..., description="VM configuration parameters")

    class Config:
        extra = 'allow'
        json_schema_extra = {
            "example": {
                "config": {
                    "name": "example-vm",
                    "memory": 2048,
                    "net0": "virtio,bridge=vmbr0",
                    "scsihw": "virtio-scsi-pci",
                    "scsi0": "local:0,import-from=/var/lib/vz/template/iso/jammy-server-cloudimg-amd64-disk-kvm.img",
                    "ide2": "local:cloudinit",
                    "boot": "order=scsi0;ide2",
                    "disk_size": "20G",
                    "serial0": "socket",
                    "vga": "serial0",
                    "ipconfig0": "ip=dhcp",
                    "agent": "enabled=1",
                    "ciuser": "sysadmin",
                    "cipassword": "Admin123456789",
                    "cicustom": "vendor=local:snippets/base.yml"
                }
            }
        }
            
