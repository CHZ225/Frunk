from flask import Blueprint, jsonify
from flask_login import login_required

bp = Blueprint("toolbox", __name__, url_prefix="/api/tools")


@bp.get("/")
@login_required
def list_tools():
    # 工具箱注册表：后端声明，前端动态渲染
    tools = [
        {
            "id": "mymo",
            "name": "Mymo 便签",
            "description": "支持标签、搜索、富文本、自动保存的笔记工具",
            "entry": {"type": "frontend_view", "view": "notes"},
        },
        {
            "id": "koculator",
            "name": "Koculator 计算器",
            "description": "基础四则运算 + 括号，支持键盘输入",
            "entry": {"type": "frontend_view", "view": "koculator"},
        },
    ]
    return jsonify(tools=tools)

