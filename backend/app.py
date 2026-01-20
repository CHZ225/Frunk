import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, send_from_directory

from extensions import cors, db, login_manager, migrate
from models import *  # noqa: F401,F403
from modules.auth import bp as auth_bp
from modules.koculator import bp as koculator_bp
from modules.mymo import bp as mymo_bp
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
    login_manager.login_view = "auth.login"

    app.register_blueprint(auth_bp)
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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✓ 数据库初始化完成")

    print("✓ 启动 Frunk: http://localhost:5003")
    app.run(debug=True, host="0.0.0.0", port=5003)

