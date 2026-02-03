from functools import wraps

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from extensions import db
from models import Announcement, PasswordResetRequest, User

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            return jsonify(error="Admin access required"), 403
        return func(*args, **kwargs)

    return wrapper


@bp.get("/users")
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    payload = [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "is_active": u.active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]
    return jsonify(users=payload)


@bp.post("/users/<int:user_id>/reset-password")
@admin_required
def reset_user_password(user_id: int):
    data = request.get_json() or {}
    new_password = data.get("password", "").strip()
    if not new_password:
        return jsonify(error="Missing password"), 400
    user = User.query.get_or_404(user_id)
    user.set_password(new_password)
    db.session.commit()
    return jsonify(message="ok")


@bp.post("/users/<int:user_id>/toggle-active")
@admin_required
def toggle_user_active(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify(error="Cannot disable your own account"), 400
    user.active = not user.active
    db.session.commit()
    return jsonify(message="ok", is_active=user.active)


@bp.get("/announcements")
@admin_required
def list_announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    payload = [
        {
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat(),
            "updated_at": a.updated_at.isoformat(),
        }
        for a in announcements
    ]
    return jsonify(announcements=payload)


@bp.get("/password-resets")
@admin_required
def list_password_resets():
    resets = PasswordResetRequest.query.order_by(PasswordResetRequest.created_at.desc()).all()
    payload = [
        {
            "id": r.id,
            "email": r.email,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in resets
    ]
    return jsonify(resets=payload)


@bp.post("/announcements")
@admin_required
def create_announcement():
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    content = data.get("content", "")
    is_active = data.get("is_active", True)
    if not title:
        return jsonify(error="Missing title"), 400
    announcement = Announcement()
    announcement.title = title
    announcement.content = content
    announcement.is_active = bool(is_active)
    announcement.created_by = current_user.id
    db.session.add(announcement)
    db.session.commit()
    return jsonify(message="ok", id=announcement.id), 201


@bp.put("/announcements/<int:announcement_id>")
@admin_required
def update_announcement(announcement_id: int):
    announcement = Announcement.query.get_or_404(announcement_id)
    data = request.get_json() or {}

    title = data.get("title")
    if title is not None:
        title = title.strip()
        if not title:
            return jsonify(error="Missing title"), 400
        announcement.title = title

    if "content" in data:
        announcement.content = data.get("content", "")

    if "is_active" in data:
        announcement.is_active = bool(data.get("is_active"))

    db.session.commit()
    return jsonify(message="ok")


@bp.delete("/announcements/<int:announcement_id>")
@admin_required
def delete_announcement(announcement_id: int):
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    return jsonify(message="ok")
