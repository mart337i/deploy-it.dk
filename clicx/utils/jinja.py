"""
Jinja2 template rendering utilities.

This module provides simplified functions for rendering Jinja2 templates
from files or strings without requiring explicit environment setup.
The environment is automatically configured using the templates_dir
from your application's config.

Key features:
- Automatic environment configuration on import
- Simple template rendering from files or strings
- Proper error handling with detailed error messages
- Type annotations for better IDE integration
- Optional environment access for advanced use cases

Functions:
    render: Render a template file with given context
    render_from_string: Render a template string with given context
    load_template: Load a template file for repeated rendering
    get_environment: Access the Jinja2 environment
    set_templates_directory: Change the templates directory

Example:
    ```python
    from clicx.utils.jinja import render
    
    # Render a template with context variables
    html = render("email.html", {
        "name": "John Smith",
        "items": ["Item 1", "Item 2", "Item 3"]
    })
    
    # Render a template string
    message = render_from_string("Hello {{ name }}!", {"name": "World"})
    ```
"""
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

from jinja2 import (
    Environment, 
    FileSystemLoader, 
    Template, 
    TemplateError, 
    select_autoescape,
    ChoiceLoader
)

from clicx import addons,templates_dir

def _setup_jinja_environment():
    def discover_template_dirs() -> List[Path]:
        addon_template_dirs = []
        
        if addons.exists() and addons.is_dir():
            for addon_dir in addons.iterdir():
                if addon_dir.is_dir():
                    # Check if this addon has a templates directory
                    addon_templates_path = addon_dir / 'templates'
                    if addon_templates_path.exists() and addon_templates_path.is_dir():
                        addon_template_dirs.append(addon_templates_path)
        
        return addon_template_dirs
    
    addons_temp = discover_template_dirs() + [templates_dir]

    loaders = [FileSystemLoader(path.absolute()) for path in addons_temp]

    env = Environment(
        loader=ChoiceLoader(loaders),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )
    
    return env

def render(template_name: str, context: Optional[Dict[str, Any]] = {}) -> str:
    """
    Render a template from the filesystem.
    """
    try:
        template = _env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        raise TemplateError(f"Failed to render template '{template_name}': {str(e)}") from e

def render_from_string(template_str: str, context: Optional[Dict[str, Any]] = {}) -> str:
    """
    Render a template from a string.
    """
    try:
        template = Environment().from_string(template_str)
        return template.render(**context)
    except Exception as e:
        raise TemplateError(f"Failed to render template string: {str(e)}") from e

def load_template(template_name: str) -> Template:
    try:
        return _env.get_template(template_name)
    except Exception as e:
        raise TemplateError(f"Failed to load template '{template_name}': {str(e)}") from e

def get_environment() -> Environment:
    return _env

def set_environment(environment : Environment) -> Environment:
    global _env
    _env = environment
    return _env

_env = _setup_jinja_environment()
