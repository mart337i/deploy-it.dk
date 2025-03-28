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

class VirtualMachineCI(BaseModel):
    vmid: int = Field(..., description="Unique identifier for the VM in Proxmox.")
    name: str = Field(..., description="Name of the virtual machine.")
    memory: int = Field(..., description="Amount of RAM in megabytes.")
    cores: int = Field(..., description="Number of CPU cores.")
    net0: str = Field(..., description="Network configuration for the VM.")
    sshkeys: Optional[str] = Field(None, description="List of SSH public keys for user authentication.")
    ciuser: Optional[str] = Field(None, description="Username for the Cloud-Init configuration.")
    cipassword: Optional[str] = Field(None, description="Optional password for the Cloud-Init user.")
    ipconfig0: Optional[str] = Field(None, description="Optional IP configuration for the VM.")
    scsi0: Optional[str] = Field(None, description="Storage configuration for the VM.")
    scsihw: Optional[str] = Field(None, description="scsihw")
    ide2: Optional[str] = Field(None, description="Cloud-init configuration for the VM.")
    boot: Optional[str] = Field(None, description="Boot order for the VM.")
    agent: Optional[str] = Field(None, description="Proxmox agent configuration.")
    cicustom: Optional[str] = Field(None, description="Custom Cloud-Init snippet for the VM.")

    class Config:
        extra = 'allow'
        json_schema_extra = {
            "example": {
                "vmid": 200,
                "name": "test-vm",
                "cores": 4,
                "memory": 8192,
                "scsihw": "virtio-scsi-pci",
                "scsi0": "local:iso/noble-server-cloudimg-amd64.img",
                "ide2": "local:cloudinit",
                "boot": "order=scsi0",
                "net0": "virtio,bridge=vmbr0",
                "ipconfig0": "ip=dhcp",
                "agent": "enabled=1",
                "sshkeys": 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIArQk8YlZR7RseAQH42utnPRqo10xANdDpruL+UcFiaZ mart337i@gmail.com',
                "ciuser": "admin",
                "cipassword": "securepassword",
                "cicustom": "user=local:snippets/ubuntu_ci2.yml",
            }
        }

class VmCloudInit(BaseModel):
    config: Dict[str, Any] = Field(..., description="VM configuration parameters")

    class Config:
        extra = 'allow'
        json_schema_extra = {
            "example": {
                "config": {
                    "vmid": 100,
                    "name": "example-vm",
                    "memory": 2048,
                    "net0": "virtio,bridge=vmbr0",
                    "scsihw": "virtio-scsi-pci",
                    "scsi0": "local:0,import-from=/var/lib/vz/template/iso/jammy-server-cloudimg-amd64-disk-kvm.img",
                    "ide2": "local:cloudinit",
                    "boot": "order=scsi0;ide2",
                    "serial0": "socket",
                    "vga": "serial0",
                    "ipconfig0": "ip=dhcp",
                    "agent": "enabled=1",
                    "ciuser": "sysadmin",
                    "cipassword": "Admin123456789",
                    "cicustom": "vendor=local:snippets/ubuntu_ci2.yml"
                }
            }
        }