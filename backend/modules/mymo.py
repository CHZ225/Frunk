from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import or_

from extensions import db
from models import Note, Tag

bp = Blueprint("mymo", __name__, url_prefix="/api/notes")


@bp.get("/")
@login_required
def list_notes():
    search = request.args.get("search", "").strip()
    tag_id = request.args.get("tag_id", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    per_page = max(1, min(per_page, 100))

    query = Note.query.filter_by(user_id=current_user.id)
    if search:
        query = query.filter(or_(Note.title.contains(search), Note.content.contains(search)))
    if tag_id:
        query = query.filter(Note.tags.any(Tag.id == tag_id))

    query = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)

    notes = [
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "is_pinned": n.is_pinned,
            "created_at": n.created_at.isoformat(),
            "updated_at": n.updated_at.isoformat(),
            "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in n.tags],
        }
        for n in pagination.items
    ]

    return jsonify(
        {
            "notes": notes,
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }
    )


@bp.post("/")
@login_required
def create_note():
    data = request.get_json() or {}
    n = Note(user_id=current_user.id, title=data.get("title", ""), content=data.get("content", ""))

    tag_ids = data.get("tag_ids", [])
    if tag_ids:
        tags = Tag.query.filter(Tag.id.in_(tag_ids), Tag.user_id == current_user.id).all()
        n.tags = tags

    db.session.add(n)
    db.session.commit()
    return (
        jsonify({"id": n.id, "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in n.tags]}),
        201,
    )


@bp.put("/<int:nid>")
@login_required
def update_note(nid: int):
    n = Note.query.filter_by(id=nid, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}

    n.title = data.get("title", n.title)
    n.content = data.get("content", n.content)

    if "is_pinned" in data:
        n.is_pinned = data.get("is_pinned", False)

    if "tag_ids" in data:
        tag_ids = data.get("tag_ids", [])
        tags = Tag.query.filter(Tag.id.in_(tag_ids), Tag.user_id == current_user.id).all()
        n.tags = tags

    db.session.commit()
    return jsonify(
        {
            "message": "ok",
            "note": {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "is_pinned": n.is_pinned,
                "created_at": n.created_at.isoformat(),
                "updated_at": n.updated_at.isoformat(),
                "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in n.tags],
            },
        }
    )


@bp.post("/<int:nid>/toggle-pin")
@login_required
def toggle_pin_note(nid: int):
    n = Note.query.filter_by(id=nid, user_id=current_user.id).first_or_404()
    n.is_pinned = not n.is_pinned
    db.session.commit()
    return jsonify({"message": "ok", "is_pinned": n.is_pinned})


@bp.delete("/<int:nid>")
@login_required
def delete_note(nid: int):
    n = Note.query.filter_by(id=nid, user_id=current_user.id).first_or_404()
    db.session.delete(n)
    db.session.commit()
    return jsonify(message="ok")


@bp.get("/tags")
@login_required
def list_tags():
    tags = Tag.query.filter_by(user_id=current_user.id).order_by(Tag.name).all()
    return jsonify(
        [{"id": t.id, "name": t.name, "color": t.color, "note_count": len(t.notes)} for t in tags]
    )


@bp.post("/tags")
@login_required
def create_tag():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    color = data.get("color", "#007bff")
    if not name:
        return jsonify(error="标签名不能为空"), 400

    existing_tag = Tag.query.filter_by(name=name, user_id=current_user.id).first()
    if existing_tag:
        return jsonify(error="标签已存在"), 409

    tag = Tag(name=name, color=color, user_id=current_user.id)
    db.session.add(tag)
    db.session.commit()
    return jsonify({"id": tag.id, "name": tag.name, "color": tag.color, "note_count": 0}), 201


@bp.put("/tags/<int:tag_id>")
@login_required
def update_tag(tag_id: int):
    tag = Tag.query.filter_by(id=tag_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}

    name = data.get("name", "").strip()
    if name and name != tag.name:
        existing_tag = Tag.query.filter_by(name=name, user_id=current_user.id).first()
        if existing_tag:
            return jsonify(error="标签名已存在"), 409
        tag.name = name

    if "color" in data:
        tag.color = data.get("color", tag.color)

    db.session.commit()
    return jsonify(
        {"id": tag.id, "name": tag.name, "color": tag.color, "note_count": len(tag.notes)}
    )


@bp.delete("/tags/<int:tag_id>")
@login_required
def delete_tag(tag_id: int):
    tag = Tag.query.filter_by(id=tag_id, user_id=current_user.id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    return jsonify(message="ok")

