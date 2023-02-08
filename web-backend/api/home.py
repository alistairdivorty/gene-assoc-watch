import flask
from . import api


@api.route("/")
def home():
    return flask.__version__
