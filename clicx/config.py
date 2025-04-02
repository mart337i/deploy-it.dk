import glob
import json
import logging
import os

import rich
from dotenv import load_dotenv

from clicx import addons as addons_dir
from clicx import project_root
from clicx import NAME


class Configuration:
    def __init__(self, addons):
        """
        Initialize configuration by loading environment variables from all files in addons
        and from the OS environment
        
        Args:
            addons: Directory containing command modules and their environment files
        """
        self.env = {}
        self.loaded_config = {}
        self.addons = addons

        self.load_env_from_directory(directory=addons)
        self.load_config_files_from_directory(directory=addons)

        debug = os.getenv('CLICX_DEBUG', 0)
        log_level = os.getenv('LOG_LEVEL', 0)
        log_to_file = os.getenv('LOG_TO_FILE', 0)

        self.debug = bool(int(debug))
        self.log_to_file = bool(int(log_to_file))


        self._logger = self.setup_logging(app_name=NAME,log_level=log_level,log_to_file=self.log_to_file)
        self._logger.info("Initialized application configuration")
   
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
        for key, value in os.environ.items():
            self.env[key] = value

    def load_config_files_from_directory(self, directory):
        """
        Load all configuration files found in the specified directory
        
        Args:
            directory: Directory to scan for environment files
        """
        if not os.path.exists(directory):
            return
        

        configuration_files = glob.glob(os.path.join(directory, "**/*.json"),include_hidden=True, recursive=True)
        for config_file in configuration_files:
            with open(config_file, 'r') as f:
                data = json.load(f)
                self.loaded_config.update(data)
                f.close()

    def setup_logging(
            self,
            app_name='app',
            log_filename='app.log',
            log_level=logging.INFO,
            log_to_file=False
        ):
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
        logging.getLogger().handlers = []
        
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        if log_to_file:
            log_dir = os.path.join(project_root, 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(os.path.join(log_dir, log_filename))
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            
            root_logger.addHandler(file_handler)
            
            loggers = ['uvicorn', 'uvicorn.access', 'uvicorn.error', NAME]
            for logger_name in loggers:
                logger = logging.getLogger(logger_name)
                logger.handlers = []  # Clear existing handlers
                logger.setLevel(log_level)
                logger.propagate = False  # Don't propagate to root logger
                logger.addHandler(file_handler)
        else:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            
            root_logger.addHandler(console_handler)
            
            loggers = ['uvicorn', 'uvicorn.access', 'uvicorn.error', NAME]
            for logger_name in loggers:
                logger = logging.getLogger(logger_name)
                logger.handlers = []  
                logger.setLevel(log_level)
                logger.propagate = False  
                logger.addHandler(console_handler)
        
        app_logger = logging.getLogger(NAME)
        app_logger.info(f"{app_name} logging system initialized")
        
        return app_logger
        
configuration: Configuration = Configuration(addons_dir)
