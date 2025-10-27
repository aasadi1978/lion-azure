from flask import Blueprint, jsonify, session
from flask import jsonify, redirect, render_template, session, url_for
from lion.logger.exception_logger import log_exception

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    try:
        if not session.get("current_user", {}):
            return redirect("/login-callback")

        return redirect(url_for('ui.loading_schedule'))

    except Exception:
        return render_template('message.html', 
                        message=jsonify({'error': log_exception('Home page failed.')}))

@home_bp.route("/health-check", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@home_bp.route("/login-callback")
def login_callback():

    try:
        from lion.orm.user import User
        user = User.load_user()
        if not user:
            return render_template('access-denied.html')

        print('========================')
        print(user)
        print('========================')
        return redirect(url_for('ui.loading_schedule'))
    
    except Exception:
        return render_template('message.html', 
                        message=jsonify({'error': log_exception('loging-callback failed.')}))
