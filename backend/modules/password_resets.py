from flask import Blueprint, jsonify, request

from extensions import db
from models import PasswordResetRequest

bp = Blueprint("password_resets", __name__, url_prefix="/api/password-resets")


@bp.post("/")
def create_password_reset_request():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    if not email:
        return jsonify(error="Missing email"), 400

    req = PasswordResetRequest(email=email, status="pending")
    db.session.add(req)
    db.session.commit()
    return jsonify(message="ok")
