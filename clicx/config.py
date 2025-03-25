from pathlib import Path
from dotenv import load_dotenv
from typing import List
import configparser
import glob
import os
import rich

templates_dir: Path = Path(Path(__file__).parent, 'templates')
addons: Path = Path(Path(__file__).parent.parent, 'addons')

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
        self.config = {}
        self.env_variables = {}
        self.template_dirs = [templates_dir] + self.discover_template_dirs()
    
    def load_config(self, config_file):
        parser = configparser.ConfigParser()
        parser.read(config_file)
        
        for section in parser.sections():
            for option in parser.options(section):
                if section != 'DEFAULT':
                    key = f"{section}_{option}"
                else:
                    key = option
                    
                value = parser.get(section, option)
                self.config[key] = value

    def create_config(output_path):
        from clicx.utils.jinja import render
        template = render(".conf.jina")
        try:
            with open(output_path, 'w') as f:
                f.write(template)
            rich.print(f"[green]Configuration file generated at: [bold]{output_path}[/bold][/green]")
            rich.print("[yellow]Please edit the file to set your specific configuration values.[/yellow]")
        except Exception as e:
            rich.print(f"[red]Error generating configuration file: {e}[/red]")

    def discover_template_dirs(self) -> List[Path]:
        addon_template_dirs = []
        
        if addons.exists() and addons.is_dir():
            for addon_dir in addons.iterdir():
                if addon_dir.is_dir():
                    # Check if this addon has a templates directory
                    addon_templates_path = addon_dir / 'templates'
                    if addon_templates_path.exists() and addon_templates_path.is_dir():
                        addon_template_dirs.append(addon_templates_path)
        
        return addon_template_dirs
   
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
            setattr(self, key, value)
            self.env_variables[key] = value
                
    def reload(self):
        """Reload environment variables from commands directory and OS environment"""
        self.load_env_from_directory(self.commands_dir)
        
        for key, value in os.environ.items():
            setattr(self, key, value)
            self.env_variables[key] = value

configuration: Configuration = Configuration(addons)
