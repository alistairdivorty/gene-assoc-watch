from flask import Blueprint

api = Blueprint("api", __name__)

from . import home
from . import articles
