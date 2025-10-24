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
