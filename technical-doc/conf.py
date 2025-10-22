# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
# 'sphinx.ext.mathjax' is for latex math rendering

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


from os import path
from sys import path as sys_path
topPath = path.dirname(path.abspath(__file__))
sys_path.insert(0, topPath)
sys_path.insert(0, path.join(topPath, 'scripts'))

from datetime import datetime
from global_params import html_logo_path, pr_media_path, pr_app_path, pr_venv_site_packages_path, pr_html_output
from image_path_extension import setup as image_path_setup
from video_path_extension import setup as video_path_setup
import roles


# -- General configuration ---------------------------------------------------
author = 'Alireza Asadi'
project = f"LION {datetime.now().strftime('%Y-%m-%d %H:%M')}"
department = 'Road Network Planning & Engineering | FedEx Express Europe | Taurusavenue 111 | 2132 LS Hoofddorp | The Netherlands'
project_copyright = f'2024 alireza.asadi@fedex.com | {department}'

# extentions
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.mathjax']

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'venv/**', 
                    'venv-*/**', 'archive/**', 'static/**', 
                    'media/**']

html_logo = f"{html_logo_path}"
html_theme = 'classic'

html_static_path = ['static/css', 'static/js']

html_css_files = [
    'css/basic.css',
    'css/classic.css'
]

html_js_files = [
    'js/searchtools.js',
    'js/update_user_comments.js'
]


# -- Options for HTML output -------------------------------------------------
if not path.exists('dist'):
    html_output_dir= f"{pr_html_output}"
    print(f"pr_media_path does not exist!")
html_output_dir = 'dist'
html_show_copyright = True


# Configuration for the image path

img_path = f"{pr_media_path}"
video_path = f"{pr_media_path}"

# The root document.
master_doc = 'index'

# Function to set up custom directives
def setup(app):
    # Set up the image directive
    image_path_setup(app)
    
    # Ensure the image path configuration is only added once
    if not hasattr(app.config, 'img_path'):
        app.add_config_value('img_path', img_path, 'env')


    video_path_setup(app)
    # Ensure the image path configuration is only added once
    if not hasattr(app.config, 'video_path'):
        app.add_config_value('video_path', video_path, 'env')


if path.exists(pr_app_path) and path.exists(pr_venv_site_packages_path):
    
    # -- Path setup to enable automodule for src code in other env ------------------------
    # Add the 'app' directory as well as the site-packages in gbd_envLion to sys.path
    # so that the .. automodule:: directive can find the modules in the source code
    sys_path.insert(0, path.abspath(pr_app_path))
    venv_path = path.abspath(pr_venv_site_packages_path)
    sys_path.insert(0, venv_path)

    # -- End of Path setup to enable automodule for src code in other env ----------------

else:
    print(f"pr_app_path and/or pr_venv_site_packages_path does not exist!")