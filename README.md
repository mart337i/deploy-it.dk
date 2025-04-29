# Deploy-it.dk Deployment Guide

## Introduction

This documentation provides step-by-step instructions for setting up the Deploy-it.dk deployment infrastructure. The guide covers Proxmox VM configuration, API setup, database configuration, and important usage notes. By following these instructions, you'll be able to establish a complete deployment environment for hosting virtual private servers with different resource configurations.

## Table of Contents
- [Proxmox VM Configuration](#proxmox-vm-configuration)
  - [Available VM Configurations](#available-vm-configurations)
  - [VM Creation Commands](#vm-creation-commands)
  - [Post-Configuration Steps](#post-configuration-steps)
- [API Setup](#api-setup)
- [Database Configuration](#database-configuration)
  - [ORM Model Definition](#orm-model-definition)
- [Usage Guidelines](#usage-guidelines)
  - [File Loading](#file-loading)
  - [Command Loading](#command-loading)
  - [Route Loading](#route-loading)
- [Notes](#notes)
- [Acknowledgements](#acknowledgements)
- [Troubleshooting](#troubleshooting)

## Proxmox VM Configuration

### Available VM Configurations

| Configuration ID | Name | Memory (GB) | CPU Cores |
|-----------------|------|------------|-----------|
| 9000 | Default VM Config | 2 | 2 |
| 9100 | Basic VPS | 4 | 2 |
| 9200 | Standard VPS | 8 | 4 |
| 9300 | Premium VPS | 16 | 8 |

### VM Creation Commands

Each configuration must be created on all Proxmox nodes.

#### Default VM Config (ID: 9000)
```bash
qm create 9000 --memory 2048 --core 2 --name default-vm-config --net0 virtio,bridge=vmbr0
qm disk import 9000 noble-server-cloudimg-amd64.img local
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local:0,import-from=local:9000/vm-9000-disk-0.raw
qm set 9000 --ide2 local:cloudinit
qm set 9000 --boot c --bootdisk scsi0
qm set 9000 --serial0 socket --vga serial0
```

#### Basic VPS (ID: 9100)
```bash
qm create 9100 --memory 4096 --core 2 --name basic-vps --net0 virtio,bridge=vmbr0
qm disk import 9100 noble-server-cloudimg-amd64.img local
qm set 9100 --scsihw virtio-scsi-pci --scsi0 local:0,import-from=local:9100/vm-9100-disk-0.raw
qm set 9100 --ide2 local:cloudinit
qm set 9100 --boot c --bootdisk scsi0
qm set 9100 --serial0 socket --vga serial0
```

#### Standard VPS (ID: 9200)
```bash
qm create 9200 --memory 8192 --core 4 --name standard-vps --net0 virtio,bridge=vmbr0
qm disk import 9200 noble-server-cloudimg-amd64.img local
qm set 9200 --scsihw virtio-scsi-pci --scsi0 local:0,import-from=local:9200/vm-9200-disk-0.raw
qm set 9200 --ide2 local:cloudinit
qm set 9200 --boot c --bootdisk scsi0
qm set 9200 --serial0 socket --vga serial0
```

#### Premium VPS (ID: 9300)
```bash
qm create 9300 --memory 16384 --core 8 --name premium-vps --net0 virtio,bridge=vmbr0
qm disk import 9300 noble-server-cloudimg-amd64.img local
qm set 9300 --scsihw virtio-scsi-pci --scsi0 local:0,import-from=local:9300/vm-9300-disk-0.raw
qm set 9300 --ide2 local:cloudinit
qm set 9300 --boot c --bootdisk scsi0
qm set 9300 --serial0 socket --vga serial0
```

### Post-Configuration Steps

Install the QEMU guest agent:
```bash
sudo apt install qemu-guest-agent -y 
```

Reset the machine ID to ensure proper machine identification when cloning:
```bash  
sudo rm -f /etc/machine-id
sudo touch /etc/machine-id

sudo rm -f /var/lib/dbus/machine-id
sudo ln -s /etc/machine-id /var/lib/dbus/machine-id
``` 

After completing these steps, shut down the template VM. When cloning from this VM, each clone will get a new machine ID.

## API Setup

Set up a Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Poetry for dependency management:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Install dependencies:
```bash
poetry install
```

Install the package in development mode:
```bash
pip install -e .
```

See available commands
```bash
clicx --help
```

## Database Configuration

Install PostgreSQL:
```bash
sudo apt install postgresql postgresql-client
```

Create a database user and database:
```bash
sudo -u postgres createuser -d -R -S $USER
createdb $USER
```

### ORM Model Definition

Example of defining a model for the ORM:
```python
from sqlalchemy import Column, Integer, String

# Import the database model
from clicx.database import models

class User(models.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
```

## Usage Guidelines

### File Loading
- All `.env` files in the `addons` folder will be automatically loaded
- All `.json` files in the `addons` folder will be automatically loaded

### Command Loading
- All commands will be loaded from the `cli` directory inside the `addons` folder
- Use `app = typer.Typer(help="Test commands")` as the variable name for proper command loading

### Route Loading
- All routes will be loaded from the `addons` folder
- Use `router = APIRouter()` as the variable name for proper route loading

## Notes

- The API timeout is set to 30 seconds instead of the default 5 seconds
- Boot time on Ubuntu is slowed by `systemd-networkd-wait-online`
  - Possible fix: See [this Ask Ubuntu thread](https://askubuntu.com/questions/1511087/systemd-networkd-wait-online-service-timing-out-during-boot)

## Acknowledgements

### Techno Tim
Thanks to Techno Tim for his blog post: https://technotim.live/posts/cloud-init-cloud-image/

## Troubleshooting

For issues with machine IDs when cloning VMs, use the modified approach:
```bash
sudo rm -f /etc/machine-id
sudo touch /etc/machine-id

sudo rm -f /var/lib/dbus/machine-id
sudo ln -s /etc/machine-id /var/lib/dbus/machine-id
```

This ensures that each cloned VM will generate a new machine ID instead of requiring manual creation with `sudo systemd-machine-id-setup`.
