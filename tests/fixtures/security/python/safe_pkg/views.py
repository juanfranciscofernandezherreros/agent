# Corpus: vista que delega en un módulo del mismo paquete.
import helpers
from flask import Blueprint, request

bp = Blueprint("users", __name__)


@bp.route("/user")
def user():
    username = request.form.get("username")
    return str(helpers.find_user(username))
