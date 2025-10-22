import os
from pathlib import Path

def generate(dir_path=Path(".").resolve(), prefix=""):
    """The module genenrate a tree-style .md document of a directory.
    """

    entries = sorted(os.listdir(dir_path))
    entries = [e for e in entries if not e.startswith('.')]
    entries = [e for e in entries if e not in ['.venv', 'venv', '__archive__', '.git', '__pycache__', 'lion.egg-info']]
    entries = [e for e in entries if not e.lower().startswith('venv-')]
    
    tree_str = ""

    for i, entry in enumerate(entries):

        full_path = os.path.join(dir_path, entry)
        connector = "└── " if i == len(entries) - 1 else "├── "
        tree_str += f"{prefix}{connector}{entry}\n"

        if os.path.isdir(full_path):
            extension = "    " if i == len(entries) - 1 else "│   "
            tree_str += generate(full_path, prefix + extension)


    return tree_str

if __name__ == '__main__':

    dir_path = Path(".").resolve() / 'src'
    if not dir_path.exists():
        print(f'Error: Directory {dir_path} does not exist.')
        exit(1)

    project_name = 'LION_UK_APP'

    tree_str = generate(dir_path=dir_path)

    output_file = 'project_tree_view.txt'
    if os.path.exists(output_file):
        os.remove(output_file)

    # Generate and save the tree
    tree_output = f"{project_name}/\n" + tree_str

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(tree_output)