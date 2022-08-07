from flask import Flask
from webapp.config import Config

app = Flask(__name__)
app.config.from_object(Config)

from webapp import routes  # noqa
