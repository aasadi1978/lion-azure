from docutils import nodes
from docutils.parsers.rst import roles


def text_danger(name, rawtext, text, lineno, inliner, options={}, content=[]):
    node = nodes.raw('', f'<span style="color: red;">{
                     text}</span>', format='html')
    return [node], []


roles.register_local_role('costum_alert', text_danger)
