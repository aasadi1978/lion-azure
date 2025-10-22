from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

"""
In your rst files, you can use the following directives to include images and videos:

.. videopath:: video_file.mp4
    :width: 940
    :height: 350
    :autoplay:
    :controls:
    :align: center

"""


class VideoPathDirective(SphinxDirective):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'width': directives.unchanged,
        'height': directives.unchanged,
        'autoplay': directives.flag,
        'controls': directives.flag,
        'loop': directives.flag,
        'muted': directives.flag,
        'align': directives.unchanged
    }

    def run(self):
        env = self.env
        video_path = env.config.video_path
        video_file = self.arguments[0]

        # Build the options dictionary for the video node
        options = {
            'uri': f"{video_path}/{video_file}",
            'width': self.options.get('width'),
            'height': self.options.get('height'),
            'autoplay': 'autoplay' if 'autoplay' in self.options else None,
            'controls': 'controls' if 'controls' in self.options else None,
            'loop': 'loop' if 'loop' in self.options else None,
            'muted': 'muted' if 'muted' in self.options else None,
            'align': self.options.get('align'),
        }

        # Filter out None values from options
        options = {k: v for k, v in options.items() if v is not None}

        # Create a video node (using HTML5 <video> tag as the base)
        video_node = nodes.raw('', f"<video {self._build_html_attributes(options)}>{video_file}</video>", format='html')

        return [video_node]

    def _build_html_attributes(self, options):
        # Convert options dictionary into HTML attributes
        attributes = []
        for key, value in options.items():
            if value is None:
                continue
            if value is True:
                attributes.append(f"{key}")
            else:
                attributes.append(f'{key}="{value}"')
        return " ".join(attributes)

def setup(app):
    app.add_config_value('video_path', '', 'env')
    app.add_directive('videopath', VideoPathDirective)
