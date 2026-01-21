# Frunk 工具箱 - 程序运行逻辑与数据存储说明

## 概述

Frunk 是一个集成多种工具的Web应用，目前包含便签管理和计算器功能。采用前后端分离架构，使用Flask + Vue.js + SQLite技术栈构建。

## 程序架构

### 技术栈
- **后端**: Flask (Python Web框架)
- **前端**: Vue.js 3 (JavaScript框架)
- **数据库**: SQLite (轻量级关系数据库)
- **富文本编辑**: TinyMCE
- **样式**: 自定义CSS

### 目录结构
```
frunk/
├── backend/                 # 后端代码
│   ├── instance/           # 数据库文件目录
│   │   └── memo.db        # SQLite数据库文件
│   ├── modules/           # 功能模块
│   │   ├── auth.py       # 用户认证
│   │   ├── toolbox.py    # 工具箱管理
│   │   ├── mymo.py       # 便签功能
│   │   └── koculator.py  # 计算器功能
│   ├── tools/            # 工具实现
│   │   └── koculator.py  # 计算器核心逻辑
│   ├── app.py           # Flask应用入口
│   ├── models.py        # 数据模型定义
│   └── extensions.py    # Flask扩展配置
├── frontend/              # 前端代码
│   ├── js/
│   │   ├── app.js       # 共享工具函数
│   │   └── main.js      # Vue应用主逻辑
│   ├── index.html       # 主页面
│   ├── styles.css       # 样式文件
│   ├── logo.svg         # Logo图标
│   └── favicon.svg      # 网站图标
├── requirements.txt       # Python依赖
└── README.md             # 项目说明
```

## 启动与运行

### 1. 环境准备
```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用
```bash
# 启动后端服务
source .venv/bin/activate && python backend/app.py
```

### 3. 访问应用
打开浏览器访问: `http://localhost:5003`

## 程序运行逻辑

### 启动流程
1. **初始化Flask应用**
   - 加载配置（数据库URI、密钥等）
   - 初始化扩展（数据库、登录管理、CORS、迁移）
   - 注册蓝图（各功能模块的路由）

2. **数据库初始化**
   - 自动创建 `backend/instance/` 目录
   - 创建SQLite数据库文件 `memo.db`
   - 根据模型定义创建数据表

3. **启动Web服务器**
   - 监听端口5003
   - 开启调试模式
   - 提供静态文件服务（前端资源）

### 用户交互流程
```
访问首页 → 登录/注册 → 工具箱页面 → 选择工具 → 使用功能
```

#### 详细流程：
1. **身份验证阶段**
   - 用户访问首页，检查登录状态
   - 未登录显示登录表单
   - 用户输入邮箱密码进行登录或注册

2. **工具箱阶段**
   - 登录成功后显示可用工具列表
   - 当前包含：Mymo便签、Koculator计算器
   - 用户点击工具进入对应功能

3. **功能使用阶段**
   - **便签功能**: 创建、编辑、删除笔记，管理标签，搜索筛选
   - **计算器功能**: 输入数学表达式，执行计算

## 数据存储详解

### 数据库位置
```
backend/instance/memo.db
```
这是一个SQLite数据库文件，存储所有应用数据。

### 数据表结构

#### 1. user表 - 用户信息
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，用户唯一标识 |
| email | VARCHAR(120) | 登录邮箱，唯一索引 |
| password_hash | VARCHAR(225) | 加密后的密码 |
| created_at | DATETIME | 注册时间 |

#### 2. note表 - 笔记数据
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，笔记唯一标识 |
| user_id | INTEGER | 外键，所属用户ID |
| title | VARCHAR(200) | 笔记标题 |
| content | TEXT | 笔记内容（HTML格式） |
| is_pinned | BOOLEAN | 是否置顶 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 最后更新时间 |

#### 3. tag表 - 标签数据
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，标签唯一标识 |
| name | VARCHAR(50) | 标签名称 |
| color | VARCHAR(7) | 标签颜色（十六进制） |
| user_id | INTEGER | 外键，所属用户ID |
| created_at | DATETIME | 创建时间 |

#### 4. note_tags表 - 笔记标签关联
| 字段 | 类型 | 说明 |
|------|------|------|
| note_id | INTEGER | 外键，笔记ID |
| tag_id | INTEGER | 外键，标签ID |

**注意**: 这是一个多对多关系表，一个笔记可以有多个标签，一个标签可以关联多个笔记。

### 数据关系
```
User (1) ←→ (N) Note
User (1) ←→ (N) Tag  
Note (N) ←→ (N) Tag (通过note_tags表)
```

## API接口文档

### 认证相关 (`/api/auth/`)
- `POST /register` - 用户注册
  - 请求体: `{email, password}`
  - 响应: `{message: "ok"}`

- `POST /login` - 用户登录
  - 请求体: `{email, password, remember?}`
  - 响应: `{message: "ok", user: {id, email}}`

- `GET /me` - 获取当前用户信息
  - 响应: `{user: {id, email}}`

- `POST /logout` - 用户退出
  - 响应: `{message: "ok"}`

### 工具箱 (`/api/tools/`)
- `GET /` - 获取可用工具列表
  - 响应: `{tools: [{id, name, description, entry}]}`

### 便签功能 (`/api/notes/`)
- `GET /` - 获取笔记列表
  - 查询参数: `search`, `tag_id`, `page`, `per_page`
  - 响应: `{notes, total, pages, page, per_page}`

- `POST /` - 创建新笔记
  - 请求体: `{title?, content?, tag_ids?}`
  - 响应: `{id, tags}`

- `PUT /<id>` - 更新笔记
  - 请求体: `{title?, content?, is_pinned?, tag_ids?}`
  - 响应: `{message: "ok", note}`

- `DELETE /<id>` - 删除笔记
  - 响应: `{message: "ok"}`

- `POST /<id>/toggle-pin` - 切换置顶状态
  - 响应: `{message: "ok", is_pinned}`

### 标签管理 (`/api/notes/tags/`)
- `GET /` - 获取标签列表
  - 响应: `[{id, name, color, note_count}]`

- `POST /` - 创建标签
  - 请求体: `{name, color?}`
  - 响应: `{id, name, color, note_count}`

- `PUT /<id>` - 更新标签
  - 请求体: `{name?, color?}`
  - 响应: `{id, name, color, note_count}`

- `DELETE /<id>` - 删除标签
  - 响应: `{message: "ok"}`

### 计算器 (`/api/tools/koculator/`)
- `POST /calc` - 执行计算
  - 请求体: `{expr}`
  - 响应: `{ok: true, result}` 或 `{ok: false, error}`

## 前端架构

### Vue.js应用结构
- **单页应用**: 所有功能在一个页面中通过视图切换实现
- **响应式数据**: 使用Vue的响应式系统管理应用状态
- **组件化**: 虽然目前在一个文件中，但逻辑按功能模块组织

### 主要数据状态
```javascript
{
  user: null,              // 当前登录用户
  view: "toolbox",         // 当前视图
  tools: [],               // 可用工具列表
  notes: [],               // 笔记列表
  tags: [],                // 标签列表
  calc: {expr, result},    // 计算器状态
  pagination: {},          // 分页信息
  // ... 其他状态
}
```

### 视图切换逻辑
- `view === null` → 登录页面
- `view === "toolbox"` → 工具箱页面
- `view === "notes"` → 便签功能
- `view === "koculator"` → 计算器功能

## 数据流向

### 完整数据流
```
用户操作 → Vue组件方法 → HTTP请求 → Flask路由 → 业务逻辑 → SQLAlchemy ORM → SQLite数据库
                                                                                    ↓
前端界面更新 ← Vue响应式更新 ← 状态更新 ← JSON响应 ← Flask返回 ← 数据处理 ← 数据库查询结果
```

### 具体示例（创建笔记）
1. 用户在前端填写笔记内容，点击保存
2. Vue调用 `createNote()` 方法
3. 发送 `POST /api/notes/` 请求到后端
4. Flask路由 `create_note()` 处理请求
5. 创建Note模型实例，保存到数据库
6. 返回JSON响应给前端
7. 前端更新笔记列表，刷新界面

## 安全特性

### 后端安全
- **密码加密**: 使用Werkzeug的密码哈希功能
- **会话管理**: Flask-Login提供安全的用户会话
- **CSRF保护**: 通过CORS配置限制跨域访问
- **SQL注入防护**: SQLAlchemy ORM自动防护

### 前端安全
- **XSS防护**: Vue.js自动转义用户输入
- **认证检查**: 每个API请求都检查登录状态
- **输入验证**: 前端和后端双重验证用户输入

## 扩展指南

### 添加新工具
1. 在 `backend/tools/` 创建工具实现
2. 在 `backend/modules/` 创建API模块
3. 在 `backend/modules/toolbox.py` 注册工具
4. 在前端添加对应的视图和逻辑

### 数据库迁移
使用Flask-Migrate进行数据库结构变更：
```bash
# 生成迁移文件
flask db migrate -m "描述变更"

# 应用迁移
flask db upgrade
```

## 故障排除

### 常见问题
1. **数据库文件不存在**: 确保 `backend/instance/` 目录存在
2. **依赖包缺失**: 检查虚拟环境是否激活，重新安装依赖
3. **端口占用**: 修改 `app.py` 中的端口号
4. **前端资源加载失败**: 检查静态文件路径配置

### 调试方法
- 查看Flask控制台输出
- 使用浏览器开发者工具检查网络请求
- 检查数据库文件是否正确创建和更新

---

*最后更新: 2025年1月*