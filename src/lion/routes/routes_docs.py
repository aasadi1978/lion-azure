from flask import Blueprint, send_from_directory
from lion.utils.login_required import login_required
from flask import Blueprint


from lion.config.paths import LION_STATIC_PATH

user_docs_blueprint = Blueprint('bp_docs', __name__)

@user_docs_blueprint.route('/docs/')
@login_required
def load_user_manual():
    return send_from_directory(LION_STATIC_PATH / 'user-manual', 'index.html')

@user_docs_blueprint.route('/docs/<path:filename>')
def load_user_manual_files(filename):
    return send_from_directory(LION_STATIC_PATH / 'user-manual', filename)

@user_docs_blueprint.route('/tdocs/')
def load_tech_docs():
    return send_from_directory(LION_STATIC_PATH / 'technical-docs', 'index.html')

@user_docs_blueprint.route('/tdocs/<path:filename>')
def load_tech_docs_files(filename):
    return send_from_directory(LION_STATIC_PATH / 'technical-docs', filename)
