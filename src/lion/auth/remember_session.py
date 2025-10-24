from datetime import timedelta
from flask import Flask, session

""" 
If you want the user to come back tomorrow and still see their last selected scenario (active_scn_id),
you can mark the session as permanent:
Now Flask stores the cookie with an expiration time 7 days from now.

Effect:

User closes browser → comes back tomorrow → still has same session["active_scn_id"].

After 7 days (or manual logout), the session expires.

Perfect for “remember my last selected scenario” behavior.

However,

# If you’re running this on Azure App Service or Kubernetes,
# and expect multiple app instances or high load,
# you should not rely solely on Flask’s cookie sessions.
# Instead, use Flask-Session or similar with Azure Redis Cache (or Cosmos DB):

from datetime import timedelta
from os import getenv

import redis
from lion.create_flask_app.create_app import LION_FLASK_APP as app
from flask_session import Session

app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_USE_SIGNER"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SESSION_REDIS"] = redis.from_url(getenv("REDIS_URL"))

Session(app)


"""
def make_session_permanent(app: Flask):
    """Make the user session permanent with a lifetime of 7 days."""
    @app.before_request
    def make_permanent():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(days=7)