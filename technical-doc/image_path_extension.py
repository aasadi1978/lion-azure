from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

"""
We want to setup a directive 'imagepath' to replace default 'image' directive.
To do that add the following lines to conf.py:

------------ conf.py -----------------------------------

from sys import path as sys_path
from scripts.image_path_extension import setup as image_path_setup

sys_path.insert(0, path.abspath('.'))
img_path = f"{pr_img_path}"
master_doc = 'index'

def setup(app):
    image_path_setup(app)
    if not hasattr(app.config, 'img_path'):
        app.add_config_value('img_path', img_path, 'env')

-----------------------------------------------------------

Below we explain the process:

The new directive will have a default path, i.e., pr_img_path, such that we use it as follows, i.e., without the path:

 .. imagepath:: image_file.png
   :width: 940
   :height: 350

To do that, we import image_path_setup function

- Add the current directory to the sys.path so that the custom directive can be imported
sys_path.insert(0, path.abspath('.'))

- Configuration for the image path
  img_path = f"{pr_img_path}"

- The root document.
  master_doc = 'index'

- Create a setup Function to set up all custom directives
    def setup(app):
        Call the setup function from your custom directive
        image_path_setup(app)
        Ensure the image path configuration is only added once
        if not hasattr(app.config, 'img_path'):
            app.add_config_value('img_path', img_path, 'env')

"""

class ImagePathDirective(SphinxDirective):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'width': directives.unchanged,
        'height': directives.unchanged,
        'alt': directives.unchanged,
        'align': directives.unchanged
    }

    def run(self):
        
        env = self.env
        img_path = env.config.img_path
        image_file = self.arguments[0]

        options = {
            'uri': f"{img_path}/{image_file}",
            'width': self.options.get('width'),
            'height': self.options.get('height'),
            'alt': self.options.get('alt', ''),
            'align': self.options.get('align', 'center'),
        }

        image_node = nodes.image(**options)

        return [image_node]

def setup(app):
    
    app.add_config_value('img_path', '', 'env')
    app.add_directive('imagepath', ImagePathDirective)
