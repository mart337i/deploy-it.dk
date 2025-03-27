from dotenv import load_dotenv
import glob
import os
import rich
from clicx import addons as addons_dir
from clicx.utils.jinja import render
import rich


class Configuration:
    def __init__(self, addons):
        """
        Initialize configuration by loading environment variables from all files in addons
        and from the OS environment
        
        Args:
            addons: Directory containing command modules and their environment files
        """
        debug = os.getenv('CLICX_DEBUG', 0)
        self.addons = addons
        self.debug = 1 if debug == 1 else 0;
        self.env = {}
        self.load_env_from_directory(directory=addons)
   
    def load_env_from_directory(self, directory):
        """
        Load all environment files found in the specified directory
        
        Args:
            directory: Directory to scan for environment files
        """
        if not os.path.exists(directory):
            return
            
        env_files = glob.glob(os.path.join(directory, "**/*.env"),include_hidden=True, recursive=True)
        for env_file in env_files:
            load_dotenv(env_file, override=True)
            rich.print(f"Loaded env file: {env_file}")
            
        for key, value in os.environ.items():
            self.env[key] = value

configuration: Configuration = Configuration(addons_dir)
