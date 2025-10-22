from os import makedirs, path as os_path
from pathlib import Path

# Setting up the paths

# Specify the path to the user manual directory. It is by default set to TEMP_Sphinx_Dist in userprofile
# To change the path, user should modify the s_phinx-build-execute.bat file

pr_html_output= 'dist'
if not os_path.exists('dist'):
    makedirs('dist', exist_ok=True)

current_dir = os_path.dirname(__file__)
TopFolder = Path(__file__).parent.resolve().parent.resolve()

pr_app_path = TopFolder / 'src' / 'lion'
pr_venv_site_packages_path = TopFolder / 'venv' / 'Lib' / 'site-packages'

# Setting up the paths: in pr_media_path, we store both images and videos

if os_path.exists('media'):
    pr_media_path = Path('media').resolve()
else:
    pr_media_path = pr_app_path / 'static' / 'images'

# Specify a logo for the HTML output
html_logo_path = Path('logo') / 'logo.png'
