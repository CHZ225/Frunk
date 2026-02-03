from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from extensions import db
from models import User

bp = Blueprint("profile", __name__, url_prefix="/api/profile")


@bp.get("/")
@login_required
def get_profile():
    return jsonify(
        profile={
            "email": current_user.email,
            "display_name": current_user.display_name,
            "phone": current_user.phone,
            "bio": current_user.bio,
            "avatar_url": current_user.avatar_url,
            "created_at": current_user.created_at.isoformat(),
        }
    )


@bp.put("/")
@login_required
def update_profile():
    data = request.get_json() or {}
    current_user.display_name = (data.get("display_name") or "").strip()
    current_user.phone = (data.get("phone") or "").strip()
    current_user.bio = (data.get("bio") or "").strip()
    avatar_url = data.get("avatar_url")
    if avatar_url is not None:
        current_user.avatar_url = avatar_url
    db.session.commit()
    return jsonify(message="ok")


@bp.put("/password")
@login_required
def update_password():
    data = request.get_json() or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""
    if not current_password or not new_password:
        return jsonify(error="Missing password"), 400
    if not current_user.check_password(current_password):
        return jsonify(error="Invalid current password"), 403
    current_user.set_password(new_password)
    db.session.commit()
    return jsonify(message="ok")


@bp.put("/email")
@login_required
def update_email():
    data = request.get_json() or {}
    new_email = (data.get("email") or "").strip()
    current_password = data.get("current_password") or ""
    if not new_email or not current_password:
        return jsonify(error="Missing data"), 400
    if not current_user.check_password(current_password):
        return jsonify(error="Invalid current password"), 403
    if new_email != current_user.email and User.query.filter_by(email=new_email).first():
        return jsonify(error="Email already exists"), 409
    current_user.email = new_email
    db.session.commit()
    return jsonify(message="ok", email=current_user.email)
