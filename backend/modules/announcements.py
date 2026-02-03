from flask import Blueprint, jsonify

from models import Announcement

bp = Blueprint("announcements", __name__, url_prefix="/api/announcements")


@bp.get("/")
def list_active_announcements():
    announcements = (
        Announcement.query.filter_by(is_active=True)
        .order_by(Announcement.created_at.desc())
        .all()
    )
    payload = [
        {
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "created_at": a.created_at.isoformat(),
        }
        for a in announcements
    ]
    return jsonify(announcements=payload)
