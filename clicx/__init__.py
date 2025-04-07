import sys
import os
from pkgutil import extend_path
from pathlib import Path

# NOTE: 
# This makes it posible to do `from clicx import x` instead of haveing to do the abselute path.
# This is also called a namespace package.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
__path__ = extend_path(__path__, __name__)

__version__ = '1.0.0'
VERSION: str = __version__
NAME = __name__

# Usefull paths
templates_dir: Path = Path(Path(__file__).parent, 'templates')
addons: Path = Path(Path(__file__).parent.parent, 'addons')
project_root : Path = Path(Path(__file__).parent.parent)


# NOTE: 
# This makes it so instead of hveing to write `from addons.proxmox.models.proxmox import proxmox`
# you can do `from proxmox.models.proxmox import proxmox`. 
# This is done to impove modularization 
sys.path.insert(0, str(addons))

# DO the import last, so we aviod circular imports 
from . import utils
from . import config
from . import cli
from . import server