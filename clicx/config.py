from dotenv import load_dotenv
import glob
import os
import rich
from clicx import addons
from clicx.utils.jinja import render


class Configuration:
    def __init__(self, commands_dir):
        """
        Initialize configuration by loading environment variables from all files in commands_dir
        and from the OS environment
        
        Args:
            commands_dir: Directory containing command modules and their environment files
        """
        debug = os.getenv('CLICX_DEBUG', 0)
        self.commands_dir = commands_dir
        self.debug = 1 if debug == 1 else 0;
        self.env = {}
   
    def load_env_from_directory(self, directory):
        """
        Load all environment files found in the specified directory
        
        Args:
            directory: Directory to scan for environment files
        """
        if not os.path.exists(directory):
            return
            
        env_files = glob.glob(os.path.join(directory, "**/*.env"), recursive=True)
        
        for env_file in env_files:
            load_dotenv(env_file, override=True)
            
        for key, value in os.environ.items():
            self.env[key] = value

configuration: Configuration = Configuration(addons)
