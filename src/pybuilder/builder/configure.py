import json
from os.path import exists, isfile


def _create_config(config_path: str, class_name: str, relative_script_path: str):
        
    with open(config_path, 'w') as f:
        json.dump({
            "main_script" : relative_script_path,
            "main_class": class_name
        }, f,indent=4)


def read_configuration(config_path : str) -> object:

    print(f"configuration path is {config_path}")
    if(not exists(config_path)):
        raise FileNotFoundError("Failed to read configuration, the file does not exist")

    if(not isfile(config_path)):
        raise FileNotFoundError("Failed to read configuration, the specified path does not point to a file")


    try:
        with open(config_path,'r') as f:
            config = json.load(f)
    except Exception as e:
        raise RuntimeError("Failed to parse project configuration file. Ensure that it is well formed json")
    
    # TODO use json schema
    isWellFormed = hasattr(config,'main_script') and hasattr(config,'class_name')

    return config
        