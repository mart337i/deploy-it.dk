from pydantic import BaseModel, Field
from typing import Dict, Any

class Container(BaseModel):
    container_config: Dict[str, Any] = Field(..., description="Container configuration parameters")

    class Config:
        extra = 'allow'
        json_schema_extra = {
            "example": {
                "container_config": {
                    'features': 'nesting=1',
                    'net0': 'name=eth0,bridge=vmbr0,firewall=1,ip=dhcp,ip6=auto,type=veth',
                    'unprivileged': 1,
                    'rootfs': 'local:8',
                    'ostemplate' : 'local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst',
                    'digest': 'efec7ba2dcb2dc715bf523188c9620d6c6bc2cfa',
                    'memory': 2048,
                    'swap': 2048,
                    'cores': 4,
                    'arch': 'amd64',
                    'ostype': 'ubuntu',
                    'hostname': 'Con',
                    'password': 'admin1234'
                }
            }
        }