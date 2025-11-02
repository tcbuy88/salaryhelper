# 数据库设计文档

## 概述
SalaryHelper使用SQLite数据库存储用户数据、会话信息、消息记录、文件附件、模板、生成的文档和订单信息。

## 数据表结构

### 1. users - 用户表
存储用户基本信息

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | 用户唯一标识（UUID） |
| phone | TEXT | UNIQUE NOT NULL | 手机号 |
| name | TEXT | | 用户名称 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 2. conversations - 会话表
存储用户与AI的对话会话

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | 会话唯一标识（UUID） |
| user_id | TEXT | NOT NULL, FOREIGN KEY | 所属用户ID |
| title | TEXT | NOT NULL | 会话标题 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 3. messages - 消息表
存储会话中的消息记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | 消息唯一标识（UUID） |
| conversation_id | TEXT | NOT NULL, FOREIGN KEY | 所属会话ID |
| sender | TEXT | NOT NULL | 发送者类型（user/ai） |
| sender_id | TEXT | | 发送者ID（用户消息时填充） |
| content | TEXT | NOT NULL | 消息内容 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 4. attachments - 附件表
存储上传的文件信息

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | 附件唯一标识（UUID） |
| file_name | TEXT | NOT NULL | 文件名 |
| content_type | TEXT | | MIME类型 |
| size_bytes | INTEGER | | 文件大小（字节） |
| storage_url | TEXT | | 存储路径 |
| preview_url | TEXT | | 预览URL |
| metadata | TEXT | | 元数据（JSON格式） |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 5. templates - 模板表
存储文书生成模板

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | 模板唯一标识（UUID） |
| name | TEXT | NOT NULL | 模板名称 |
| description | TEXT | | 模板描述 |
| category | TEXT | | 分类（仲裁/工资/合同等） |
| content | TEXT | NOT NULL | 模板内容（支持变量替换） |
| fields | TEXT | | 必填字段列表（JSON数组） |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**预置模板**：
- tpl-001: 劳动仲裁申请书
- tpl-002: 工资支付申诉书
- tpl-003: 劳动合同解除通知书

### 6. documents - 文档表
存储用户生成的文档

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | 文档唯一标识（UUID） |
| user_id | TEXT | NOT NULL, FOREIGN KEY | 所属用户ID |
| template_id | TEXT | FOREIGN KEY | 使用的模板ID |
| title | TEXT | NOT NULL | 文档标题 |
| content | TEXT | NOT NULL | 文档内容（填充后） |
| status | TEXT | DEFAULT 'draft' | 状态（draft/completed） |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 7. orders - 订单表
存储支付订单信息

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | 订单唯一标识（UUID） |
| user_id | TEXT | NOT NULL, FOREIGN KEY | 所属用户ID |
| product_type | TEXT | NOT NULL | 产品类型（consultation/document/service） |
| product_id | TEXT | | 产品ID（如文档ID） |
| amount | REAL | NOT NULL | 金额 |
| status | TEXT | DEFAULT 'pending' | 状态（pending/paid/cancelled） |
| payment_method | TEXT | | 支付方式（wechat/alipay） |
| transaction_id | TEXT | | 交易流水号 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| paid_at | TIMESTAMP | | 支付完成时间 |

## 数据关系

```
users (1) ─────── (N) conversations
                      │
                      └─── (N) messages

users (1) ─────── (N) documents
                      │
templates (1) ────────┘

users (1) ─────── (N) orders
```

## 索引建议

建议在生产环境中添加以下索引以提升查询性能：

```sql
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
```

## 数据库初始化

数据库在应用启动时自动初始化，包括：
1. 创建所有表结构
2. 插入预置的文书模板
3. 设置外键约束

数据库文件位置：`/tmp/salaryhelper.db`

## 备份和迁移

对于生产环境，建议：
1. 定期备份SQLite数据库文件
2. 考虑迁移到PostgreSQL或MySQL以支持更高并发
3. 使用Alembic进行数据库版本管理和迁移

## 数据清理

开发和测试环境可以通过删除数据库文件重置：
```bash
rm /tmp/salaryhelper.db
```
应用重启后会自动重新初始化数据库。
