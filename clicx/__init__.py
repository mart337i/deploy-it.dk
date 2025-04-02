import sys
import os
from pkgutil import extend_path
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

__path__ = extend_path(__path__, __name__)

__version__ = '1.0.0'
VERSION: str = __version__

# Usefull paths
templates_dir: Path = Path(Path(__file__).parent, 'templates')
addons: Path = Path(Path(__file__).parent.parent, 'addons')
project_root : Path = Path(Path(__file__).parent.parent)

if addons.exists():
    sys.path.insert(0, str(addons))

from . import utils
from . import config
from . import cli
from . import server