# SalaryHelper - 劳动纠纷助手 Demo

SalaryHelper是一个劳动法咨询助手Demo，提供手机号验证码登录、AI对话聊天、文书生成、文件上传和支付模拟等功能。

## 🚀 快速开始

### 方式一：一键启动（推荐）
```bash
./start_demo.sh
```

### 方式二：手动启动
```bash
# 启动后端服务
cd server
source .venv/bin/activate
python app/main.py

# 在浏览器中打开前端页面
open static/index.html
```

### 方式三：Docker部署
```bash
docker compose -f docker-compose-full.yml up --build
```

## 📱 访问地址

### 前端页面
- **主页**: `file://$(pwd)/static/index.html`
- **登录**: `file://$(pwd)/static/login.html`
- **会话**: `file://$(pwd)/static/conversations.html`
- **知识库**: `file://$(pwd)/static/kb.html`
- **文书生成**: `file://$(pwd)/static/docgen.html`
- **证据管理**: `file://$(pwd)/static/evidence.html`
- **支付模拟**: `file://$(pwd)/static/payment.html`
- **用户中心**: `file://$(pwd)/static/me.html`
- **管理后台**: `file://$(pwd)/static/admin/index.html`

### 后端API
- **API服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

## 🔐 测试账号

- **手机号**: 13800000000
- **验证码**: 123456

## ✨ 功能特性

### 已实现功能
- ✅ **手机号验证码登录** - 模拟短信验证
- ✅ **JWT认证系统** - 安全的token认证
- ✅ **会话管理** - 创建、查看、管理对话会话
- ✅ **AI对话聊天** - 实时消息发送和AI回复（模拟）
- ✅ **文件上传系统** - 文件上传和附件管理
- ✅ **文书生成** - 基于模板的文档自动生成
- ✅ **模板管理** - 预置劳动法文书模板（仲裁申请书、工资申诉书、合同解除通知等）
- ✅ **支付系统** - 订单创建和支付模拟（微信/支付宝）
- ✅ **管理后台** - 用户、会话、订单管理和数据统计
- ✅ **响应式UI** - 支持桌面和移动端
- ✅ **数据持久化** - SQLite数据库存储

### 待完善功能
- 🔄 **前端界面** - 文书生成、支付、管理后台的UI页面
- 🔄 **AI集成** - 接入真实AI模型和RAG知识库
- 🔄 **文件预览** - 上传文件的在线预览功能
- 🔄 **模板编辑器** - 可视化模板编辑界面

## 🛠 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite
- **认证**: JWT (python-jose)
- **部署**: Docker + Uvicorn

### 前端
- **技术**: 原生HTML/CSS/JavaScript
- **样式**: 自定义CSS，符合设计规范
- **API**: Fetch API + async/await

## 📁 项目结构

```
salaryhelper/
├── server/                 # 后端服务
│   ├── app/
│   │   └── main.py        # FastAPI主应用
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile         # Docker配置
├── static/                # 前端静态文件
│   ├── api-client-real.js # 真实API客户端
│   ├── login.html         # 登录页面
│   ├── index.html         # 主页
│   ├── conversations.html # 会话页面
│   ├── styles.css         # 样式文件
│   └── ...               # 其他页面
├── docs/                  # 项目文档
│   ├── DEPLOYMENT_PLAN.md # 部署方案指南
│   ├── API_REFERENCE.md   # API参考文档
│   ├── database-design.md # 数据库设计
│   └── ...               # 其他文档
├── test_api.py           # API测试脚本
├── start_demo.sh         # 一键启动脚本
└── README.md             # 项目说明
```

## 🧪 测试

### API测试
```bash
python test_api.py
```

### 手动测试流程
1. 访问登录页面
2. 输入手机号 13800000000
3. 点击发送验证码（会显示 123456）
4. 输入验证码完成登录
5. 创建新会话
6. 发送消息测试AI回复

## 📋 开发进度

详细开发进度请查看 [DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md)

## 🚀 生产部署

### 部署指南
📖 **[完整部署方案](docs/DEPLOYMENT_PLAN.md)** - 生产环境部署蓝图，包含前端、后端、数据库、容器化、CI/CD、安全监控等完整指南

### 快速部署
```bash
# 生产环境部署
docker compose -f docker-compose.prod.yml up -d

# Kubernetes 部署
kubectl apply -f k8s/
```

### 当前版本：v0.2.0 (MVP完整版)
- ✅ Auth模块 - 100%完成
- ✅ Chat模块 - 100%完成
- ✅ 文件上传 - 100%完成
- ✅ 文书生成 - 100%完成
- ✅ 支付系统 - 100%完成
- ✅ 管理后台 - 100%完成

### MVP核心功能已完成
所有后端API已经实现并通过测试，包括：
- 用户认证和会话管理
- AI对话系统（模拟回复）
- 文书模板管理和文档生成
- 文件上传和附件管理
- 订单创建和支付流程
- 管理后台数据查询和统计

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

本项目仅供演示和学习使用。

## 📞 联系方式

如有问题或建议，请提交 Issue。

---

**注意**: 这是一个Demo项目，仅用于演示功能。生产环境使用前请进行安全评估和性能优化。
