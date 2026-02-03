from __future__ import annotations

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(225), nullable=False)
    display_name = db.Column(db.String(80), default="")
    phone = db.Column(db.String(30), default="")
    bio = db.Column(db.String(280), default="")
    avatar_url = db.Column(db.Text, default="")
    role = db.Column(db.String(20), default="user", nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, pwd: str) -> None:
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd: str) -> bool:
        return check_password_hash(self.password_hash, pwd)

    @property
    def is_active(self) -> bool:
        return self.active

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    def get_id(self) -> str:
        return str(self.id)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default="#007bff")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User", backref="tags")
    __table_args__ = (db.UniqueConstraint("name", "user_id", name="unique_user_tag"),)


note_tags = db.Table(
    "note_tags",
    db.Column("note_id", db.Integer, db.ForeignKey("note.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), default="")
    content = db.Column(db.Text, default="")
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship("User", backref="notes")
    tags = db.relationship("Tag", secondary=note_tags, backref="notes")


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))

    author = db.relationship("User")


class PasswordResetRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


@login_manager.user_loader
def load_user(user_id: str):
    user = User.query.get(int(user_id))
    if user and not user.active:
        return None
    return user
