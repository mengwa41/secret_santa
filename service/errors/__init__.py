from flask import Blueprint

bp = Blueprint('errors', __name__)

from service.errors import exceptions