from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from models import User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    data = request.get_json() or {}
    email, password = data.get("email"), data.get("password")
    if not email or not password:
        return jsonify(error="Missing data"), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify(error="Email already exists"), 409

    u = User(email=email)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return jsonify(message="ok")


@bp.post("/login")
def login():
    data = request.get_json() or {}
    email, password = data.get("email"), data.get("password")
    remember = data.get("remember", True)
    u = User.query.filter_by(email=email).first()
    if not u or not u.check_password(password):
        return jsonify(error="Invalid email or password"), 401
    login_user(u, remember=remember)
    return jsonify(message="ok", user={"id": u.id, "email": u.email})


@bp.get("/me")
@login_required
def me():
    return jsonify(user={"id": current_user.id, "email": current_user.email})


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify(message="ok")

