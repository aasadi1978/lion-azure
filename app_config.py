import os, tomllib, tomli_w
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--version", required=False)
args = parser.parse_args()

def expand_env_vars_in_toml(config: dict) -> dict:

    """Recursively replace ${VAR} in strings with environment values."""
    def expand(value):
        if isinstance(value, str):
            return os.path.expandvars(value)
        elif isinstance(value, dict):
            return {k: expand(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [expand(v) for v in value]
        else:
            return value
        
    return expand(config)

try:

    version=os.getenv('LION_APP_VERSION', args.version)

    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)

    old_version = config['project']['version']
    config['project']['version'] = version or old_version

    expanded_config = expand_env_vars_in_toml(config)

    # ---- Write back ----
    with open("pyproject.toml", "wb") as f:
        tomli_w.dump(expanded_config, f)
    
    #Verify:
    with open("pyproject.toml", "rb") as f:
        config_copied = tomllib.load(f)
    
    print(f"APP version: {config_copied['project']['version']}")

except Exception as e:
    print(f"toml expansion failed: {str(e)}")

print('------------------------------------------------------')