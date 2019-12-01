import json


def _create_config(config_path: str, class_name: str):
        
    with open(config_path, 'w') as f:
        json.dump({
            "class_name": class_name
        }, f)
