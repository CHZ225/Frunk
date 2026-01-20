# Frunk 工具箱（mymo + Koculator 整合）

目标：从**登录界面**进入，登录成功后到**工具箱界面**，选择工具（目前包含 `mymo` 便签、`Koculator` 计算器），并保留可扩展结构方便以后新增工具。

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

## 项目结构

- **后端（frunk/backend）**
  - `modules/auth.py`：登录/注册/退出模块
  - `modules/toolbox.py`：工具箱注册表 `GET /api/tools/`
  - `modules/mymo.py`：笔记模块（notes/tags）
  - `modules/koculator.py` + `tools/koculator.py`：计算器模块
- **前端（frunk/frontend）**
  - `index.html` + `js/*`：单页多模块应用
    - 登录页 -> 工具箱 -> 工具视图（notes / koculator）

> **注意**：旧的 `Koculator/` 和 `mymo/` 目录的源代码已清理，仅保留 `.git`、`.venv` 等配置目录（可手动删除）。


## 如何新增一个工具

1. 在 `frunk/backend/tools/` 新建模块（例如 `tools/mytool.py`），实现你的 API（或新增 blueprint）。
2. 在 `frunk/backend/modules/toolbox.py` 的 `tools` 列表里新增一项：
   - `id / name / description`
   - `entry.view`：前端要打开的视图名（例如 `"mytool"`）
3. 在 `frunk/frontend/index.html` + `frunk/frontend/js/main.js` 增加对应 `view` 的 UI 与逻辑。

