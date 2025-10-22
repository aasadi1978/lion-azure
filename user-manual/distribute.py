from os import getenv, path as os_path, rmdir
from shutil import copytree
from global_params import pr_html_output

pr_lion_shared_directory = getenv('LION_SHARED_DIR')

if pr_lion_shared_directory:

    dst_dir = os_path.join(
        pr_lion_shared_directory, 'UserManual')

    rmdir(dir=dst_dir)
    copytree(src=pr_html_output, dst=dst_dir)

else:
    print("pr_lion_shared_directory does not exist!")
