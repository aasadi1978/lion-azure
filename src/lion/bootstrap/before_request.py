from functools import wraps
from flask import Flask, g, redirect, render_template, session, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("access_denied"))
        
        return f(*args, **kwargs)
    
    return decorated_function


def run_before_request(app: Flask):

    with app.app_context():

        from lion.orm.groups import GroupName
    
        @app.before_request
        def load_user():
            user_id = session.get("user_id")
            if user_id:
                g.user_id = user_id
                g.groups = [g.group_name for g in GroupName.query.filter_by(user_id=user_id).all()]
                g.user = user_id
            else:
                g.user_id = None
                g.user = None
                g.groups = []


        @app.route("/login-callback")
        def login_callback():
            # Replace this with how you extract the user info
            user_id  = GroupName.set_user_scope()
            if not user_id :
                return render_template('access-denied.html')

            session["user_id"] = user_id
            return redirect(url_for('ui.loading_schedule'))

        # @app.route("/dashboard")
        # @login_required
        # def dashboard():