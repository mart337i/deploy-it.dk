import sys
import os
from pkgutil import extend_path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

__path__ = extend_path(__path__, __name__)

__version__ = '1.0.0'
VERSION: str = __version__


from . import utils
from . import config
from . import cli