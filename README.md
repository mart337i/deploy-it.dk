# Deploy-it.dk deployment API
## Setup Proxmox

## Proxmox VM Creation Guide

Here's a concise guide to creating virtual machines in Proxmox using the provided commands:

## Proxmox VPS Configuration Guide
Create the following on each of the proxmox nodes

### Available Configurations

| Configuration ID | Name | Memory (GB) | CPU Cores |
|-----------------|------|------------|-----------|
| 9000 | Default VM Config | 2 | 2 |
| 9100 | Basic VPS | 4 | 2 |
| 9200 | Standard VPS | 8 | 4 |
| 9300 | Premium VPS | 16 | 8 |

### Creation Commands

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

Now we need to install the qemu-guest-agent using:
```sh
sudo apt install qemu-guest-agent -y 
```
and then run:

```sh  
sudo rm -f /etc/machine-id
sudo touch /etc/machine-id

sudo rm -f /var/lib/dbus/machine-id
sudo ln -s /etc/machine-id /var/lib/dbus/machine-id
``` 

Then just shutdown the template vm and when cloning from the vm it will get a new machine id.

## Setup the API
```sh
python3 -m venv .venv
```

```sh
source .venv/bin/actiavte

```
```sh
curl -sSL https://install.python-poetry.org | python3 -
```

```sh
poetry install
```

```sh
pip install -e .

```
## Usage

- All .env files will be loaded if they are loacted in the addons folder
- All .json files will be loaded if they are loacted in the addons folder
- All Commands will be loaded in the cli dir inside addons folder (app = typer.Typer(help="Test commands")) Use app as the varibale name, other wise it dosent work.
- All Routes will be loaded inside the addons folder (router = APIRouter()) use router, other wise it donsent work. 


## Thanks to: 
### Techno Tim
For this blog: https://technotim.live/posts/cloud-init-cloud-image/

A small ajustment to the debug section. 
Instead of running:
```sh
sudo rm -f /etc/machine-id
sudo rm -f /var/lib/dbus/machine-id
```
Run
```sh  
sudo rm -f /etc/machine-id
sudo touch /etc/machine-id

sudo rm -f /var/lib/dbus/machine-id
sudo ln -s /etc/machine-id /var/lib/dbus/machine-id
``` 

This will enable the created template to generate a new machine id instead of haveing to create on manually using `sudo systemd-machine-id-setup
`
## Good to know:
- Boot time on ubuntu is slowed by `systemd-networkd-wait-online` 
    - Posible fix: https://askubuntu.com/questions/1511087/systemd-networkd-wait-online-service-timing-out-during-boot