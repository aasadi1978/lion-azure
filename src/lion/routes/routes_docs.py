from datetime import datetime
from flask import Blueprint, request, send_from_directory
from datetime import datetime
from json import loads as json_loads
from os import path as os_path
from lion.config.paths import LION_PROJECT_HOME, LION_SHARED_DIR
from lion.utils.login_required import login_required
from lion.logger.exception_logger import log_exception
from lion.create_flask_app.create_app import LION_FLASK_APP
from flask import Blueprint, request


from lion.config.paths import LION_STATIC_PATH
from lion.utils.popup_notifier import show_popup

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

@user_docs_blueprint.route('/update_comments', methods=['POST'])
def update_comments():

    when = datetime.now().strftime('%Y-%m-%d %H:%M')
    txt_no_line = ''

    try:

        request_data = request.form['request_data']
        request_data = json_loads(request_data)

        comnt = request_data['comment']
        filePath = request_data['filePath']
        _filename = filePath.replace(
            'http://localhost:2000/lion/docs/', '')

        section_id = request_data['sec_id']
        section_id = section_id.replace('id-user-comment-', '')

        txt_no_line = f'On {when}, {LION_FLASK_APP.config['LION_USER_FULL_NAME']} commented on {
            _filename}-{section_id}:\n{comnt}'
        txt_no_line = f"{txt_no_line}\nFilename: {os_path.join(
            LION_SHARED_DIR, 'user_manual_comments.log')}"
        txt = f"{txt_no_line}\n{'-'*100}"

        with open(os_path.join(LION_SHARED_DIR, 'user_manual_comments.log'), 'a') as _usr_f:
            _usr_f.writelines(txt)

        with open(os_path.join(LION_PROJECT_HOME, 'user_manual_comments.log'), 'a') as _usr_f:
            _usr_f.writelines(txt)

    except Exception:
        log_exception(
            popup=True, remarks='Comment was not saved!')
        return {}

    if txt_no_line != '':
        show_popup(
            f'The following comment has been successfuly saved:\n{txt_no_line}')

    return {}

