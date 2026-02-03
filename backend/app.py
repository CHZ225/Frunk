import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, send_from_directory
from sqlalchemy import inspect, text

from extensions import cors, db, login_manager, migrate
from models import *  # noqa: F401,F403
from modules.admin import bp as admin_bp
from modules.announcements import bp as announcements_bp
from modules.auth import bp as auth_bp
from modules.koculator import bp as koculator_bp
from modules.mymo import bp as mymo_bp
from modules.password_resets import bp as password_resets_bp
from modules.profile import bp as profile_bp
from modules.toolbox import bp as toolbox_bp

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    default_sqlite = f"sqlite:///{(BASE_DIR / 'instance' / 'memo.db').as_posix()}"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", default_sqlite)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["REMEMBER_COOKIE_DURATION"] = 30
    app.config["REMEMBER_COOKIE_SECURE"] = False
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5003", "http://127.0.0.1:5003"]}},
        supports_credentials=True,
    )
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # type: ignore[assignment]

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(announcements_bp)
    app.register_blueprint(password_resets_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(toolbox_bp)
    app.register_blueprint(koculator_bp)
    app.register_blueprint(mymo_bp)

    @app.get("/")
    def index():
        return send_from_directory(str(FRONTEND_DIR), "index.html")

    @app.get("/<path:path>")
    def assets(path):
        return send_from_directory(str(FRONTEND_DIR), path)

    return app


app = create_app()


def ensure_sqlite_schema():
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not uri.startswith("sqlite:"):
        return

    inspector = inspect(db.engine)
    if "user" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("user")}
    with db.session.begin():
        if "role" not in columns:
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
            )
        if "active" not in columns:
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1")
            )
        if "display_name" not in columns:
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN display_name VARCHAR(80) NOT NULL DEFAULT ''")
            )
        if "phone" not in columns:
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN phone VARCHAR(30) NOT NULL DEFAULT ''")
            )
        if "bio" not in columns:
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN bio VARCHAR(280) NOT NULL DEFAULT ''")
            )
        if "avatar_url" not in columns:
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN avatar_url TEXT NOT NULL DEFAULT ''")
            )
        db.session.execute(text("UPDATE user SET role = 'user' WHERE role IS NULL"))
        db.session.execute(text("UPDATE user SET active = 1 WHERE active IS NULL"))
        db.session.execute(text("UPDATE user SET display_name = '' WHERE display_name IS NULL"))
        db.session.execute(text("UPDATE user SET phone = '' WHERE phone IS NULL"))
        db.session.execute(text("UPDATE user SET bio = '' WHERE bio IS NULL"))
        db.session.execute(text("UPDATE user SET avatar_url = '' WHERE avatar_url IS NULL"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_sqlite_schema()
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if admin_email and admin_password:
            from models import User

            admin_user = User.query.filter_by(email=admin_email).first()
            if not admin_user:
                admin_user = User(email=admin_email, role="admin")  # type: ignore[call-arg]
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()
                print("✓ 管理员账号已创建")
            elif admin_user.role != "admin":
                admin_user.role = "admin"
                db.session.commit()
                print("✓ 管理员账号已升级")
        print("✓ 数据库初始化完成")

    print("✓ 启动 Frunk: http://localhost:5003")
    app.run(debug=True, host="0.0.0.0", port=5003)
