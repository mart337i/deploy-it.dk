import yaml
import os
import json
from typing import Dict, List, Any, Optional

def read(yml_file: str) -> Dict[str, Any]:
    try:
        with open(yml_file, 'r') as file:
            data = yaml.safe_load(file)
        return data
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        raise

def validate(yml_data: Dict[str, Any]) -> bool:
    """
    Validate if the YAML data follows the expected structure.
    
    Expected structure:
    {
        "Distribution-Version": {
            "commands": [
                "command1",
                "command2",
                ...
            ],
            "description": "Description text"
        },
        ...
    }
    """
    if not isinstance(yml_data, dict):
        print("Error: YAML data is not a dictionary")
        return False
    
    for distro, content in yml_data.items():
        if not isinstance(content, dict):
            print(f"Error: Content for {distro} is not a dictionary")
            return False
        
        if 'commands' not in content:
            print(f"Error: 'commands' key missing for {distro}")
            return False
            
        if 'description' not in content:
            print(f"Error: 'description' key missing for {distro}")
            return False
        
        if not isinstance(content['commands'], list):
            print(f"Error: 'commands' for {distro} is not a list")
            return False
        
        if not isinstance(content['description'], str):
            print(f"Error: 'description' for {distro} is not a string")
            return False
    
    return True

def write(data: Dict[str, Any], yml_file: str) -> None:
    try:
        with open(yml_file, 'w') as file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False)
        print(f"Data successfully written to {yml_file}")
    except Exception as e:
        print(f"Error writing to YAML file: {e}")
        raise

def export_to_json(yml_data: Dict[str, Any], json_file: str) -> None:
    try:
        with open(json_file, 'w') as file:
            json.dump(yml_data, file, indent=2)
        print(f"Data successfully exported to {json_file}")
    except Exception as e:
        print(f"Error exporting to JSON file: {e}")
        raise