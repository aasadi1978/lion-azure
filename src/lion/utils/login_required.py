# Will be used as decorator to inforce authentication
# @app.route("/dashboard")
# @login_required
# def dashboard():
#     ...

from flask import redirect, session, url_for
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("access_denied"))

        return f(*args, **kwargs)

    return decorated_function