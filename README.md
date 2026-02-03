# Frunk 工具箱（mymo + Koculator 整合）

目标：从**统一登录界面**进入，登录成功后根据角色进入**工具箱界面**或**管理员后台**，选择工具（目前包含 `mymo` 便签、`Koculator` 计算器），并保留可扩展结构方便以后新增工具。

## 启动方式

### 1) 安装依赖（后端）

在项目根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r frunk/requirements.txt
```

### 2) 启动整合后的应用（新入口）

```bash
python3 frunk/backend/app.py
```

然后打开：`http://localhost:5003`

### 3) 初始化管理员账号（可选）

启动前设置环境变量，将自动创建管理员账号：

```bash
export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="ChangeMe123"
```

## 项目结构

- **后端（frunk/backend）**
  - `modules/auth.py`：登录/注册/退出模块
  - `modules/admin.py`：管理员 API（公告管理、用户管理）
  - `modules/announcements.py`：公告公开接口
  - `modules/toolbox.py`：工具箱注册表 `GET /api/tools/`
  - `modules/mymo.py`：笔记模块（notes/tags）
  - `modules/koculator.py` + `tools/koculator.py`：计算器模块
  - `models.py`：新增公告模型、用户角色与状态
- **前端（frunk/frontend）**
  - `index.html` + `js/*`：单页多模块应用
    - 登录页 -> 工具箱/管理员后台 -> 工具视图（notes / koculator）

> **注意**：旧的 `Koculator/` 和 `mymo/` 目录的源代码已清理，仅保留 `.git`、`.venv` 等配置目录（可手动删除）。


## 如何新增一个工具

1. 在 `frunk/backend/tools/` 新建模块（例如 `tools/mytool.py`），实现你的 API（或新增 blueprint）。
2. 在 `frunk/backend/modules/toolbox.py` 的 `tools` 列表里新增一项：
   - `id / name / description`
   - `entry.view`：前端要打开的视图名（例如 `"mytool"`）
3. 在 `frunk/frontend/index.html` + `frunk/frontend/js/main.js` 增加对应 `view` 的 UI 与逻辑。

## 管理员功能说明

- 登录后按角色分流，管理员进入“管理员后台”视图。
- 公告管理（增删改查），公告会在工具箱主页展示。
- 用户管理：查看用户列表、重置密码、禁用账号（不显示明文密码）。

## 数据库变更说明

- `User` 新增 `role` 与 `active` 字段。
- 新增 `Announcement` 表。
- 已有数据建议执行迁移；如果不需要保留旧数据，可删除本地 `backend/instance/memo.db` 重新启动。
