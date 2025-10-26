from flask import Flask, current_app
from lion.routes.routes_runtimes import runtimes_bp
from lion.routes.routes_entry_point import top_blueprint
from lion.routes.routes_movements import movements_bp
from lion.routes.routes_ui import ui_bp
from lion.routes.routes_optimization import optim_bp
from lion.routes.routes_statusbar import statusbar_bp
from lion.routes.routes_docs import user_docs_blueprint
from lion.logger.routes_upload_logs import bp_copy_logs

# with LION_FLASK_APP.app_context():
def register_blueprints(app: Flask = current_app):
    """Register all blueprints with the Flask app."""

    app.register_blueprint(top_blueprint)
    app.register_blueprint(runtimes_bp)
    app.register_blueprint(movements_bp)
    app.register_blueprint(ui_bp)
    app.register_blueprint(statusbar_bp)
    app.register_blueprint(optim_bp)
    app.register_blueprint(user_docs_blueprint)
    app.register_blueprint(bp_copy_logs)    