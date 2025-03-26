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
        self.config = {}
        self.env_variables = {}
        
    def create_config(self,output_path):
        template = render(template_name="clicx.conf.jinja")
        try:
            with open(output_path, 'w') as f:
                f.write(template)
            rich.print(f"[green]Configuration file generated at: [bold]{output_path}[/bold][/green]")
            rich.print("[yellow]Please edit the file to set your specific configuration values.[/yellow]")
        except Exception as e:
            rich.print(f"[red]Error generating configuration file: {e}[/red]")
   
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
