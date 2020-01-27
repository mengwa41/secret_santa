from flask import Blueprint

bp = Blueprint('auth', __name__)

from service.auth import service