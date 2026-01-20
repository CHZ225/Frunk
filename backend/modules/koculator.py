from flask import Blueprint, request
from flask_login import login_required

from tools.koculator import calc_expr

bp = Blueprint("koculator", __name__, url_prefix="/api/tools/koculator")


@bp.post("/calc")
@login_required
def calc():
    payload = request.get_json(silent=True) or {}
    expr = payload.get("expr", "")
    return calc_expr(expr)

