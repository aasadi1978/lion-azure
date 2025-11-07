import os, tomllib, tomli_w
# import argparse
import sys

# parser = argparse.ArgumentParser()
# parser.add_argument("--increment-version", required=False)
# args = parser.parse_args()

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
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)

    current_version = config['project']['version']
    major, minor, patch = map(int, current_version.split('.'))

    if patch >= 99:
        patch = 0
        minor += 1

        if minor >= 99:
            minor = 0
            major += 1
    else:
        patch += 1

    version = f"{major}.{minor}.{patch}"
    config['project']['version'] = version or current_version

    expanded_config = expand_env_vars_in_toml(config)

    # ---- Write back ----
    with open("pyproject.toml", "wb") as f:
        tomli_w.dump(expanded_config, f)
    
    #Verify:
    with open("pyproject.toml", "rb") as f:
        config_copied = tomllib.load(f)
    
    print(version)

except Exception:
    print(f"Error updating version in pyproject.toml: {sys.exc_info()[0]}")
    sys.exit(1)
