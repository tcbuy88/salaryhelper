# SalaryHelper API 参考文档

## 基本信息

**Base URL**: `http://localhost:8000/api/v1`

**认证方式**: JWT Bearer Token

大部分API需要在请求头中携带认证token：
```
Authorization: Bearer {your_token}
```

**统一响应格式**:
```json
{
  "code": 0,
  "message": "success",
  "data": {...}
}
```

## API端点

### 1. 认证模块 (Auth)

#### 1.1 发送短信验证码
```
POST /auth/send-sms
```

**请求体**:
```json
{
  "phone": "13800000000"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "验证码已发送",
  "data": {
    "code": "123456"
  }
}
```

#### 1.2 用户登录
```
POST /auth/login
```

**请求体**:
```json
{
  "phone": "13800000000",
  "code": "123456"
}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": "uuid",
      "phone": "13800000000",
      "name": "User-13800000000"
    }
  }
}
```

#### 1.3 获取当前用户信息
```
GET /auth/me
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "phone": "13800000000",
    "name": "User-13800000000",
    "created_at": "2024-11-02 10:00:00"
  }
}
```

### 2. 会话和消息模块 (Conversations)

#### 2.1 创建会话
```
POST /conversations
```

**需要认证**: 是

**请求体**:
```json
{
  "title": "咨询工资纠纷"
}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "title": "咨询工资纠纷"
  }
}
```

#### 2.2 获取会话列表
```
GET /conversations
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "title": "咨询工资纠纷",
      "created_at": "2024-11-02 10:00:00"
    }
  ]
}
```

#### 2.3 获取会话详情
```
GET /conversations/{convId}
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": {
    "conversation": {
      "id": "uuid",
      "user_id": "uuid",
      "title": "咨询工资纠纷",
      "created_at": "2024-11-02 10:00:00"
    },
    "messages": [
      {
        "id": "uuid",
        "conversation_id": "uuid",
        "sender": "user",
        "sender_id": "uuid",
        "content": "我的工资被拖欠了",
        "created_at": "2024-11-02 10:01:00"
      },
      {
        "id": "uuid",
        "conversation_id": "uuid",
        "sender": "ai",
        "sender_id": null,
        "content": "我理解您的情况，请问...",
        "created_at": "2024-11-02 10:01:05"
      }
    ]
  }
}
```

#### 2.4 发送消息
```
POST /conversations/{convId}/messages
```

**需要认证**: 是

**请求体**:
```json
{
  "text": "我的工资被拖欠三个月了"
}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "message_id": "uuid",
    "status": "sent",
    "ai_reply": {
      "message_id": "uuid",
      "content": "（模拟回复）已收到您的消息..."
    }
  }
}
```

### 3. 文件上传模块 (Upload)

#### 3.1 上传文件
```
POST /upload
```

**需要认证**: 是

**请求**: multipart/form-data
- file: 文件数据

**响应**:
```json
{
  "code": 0,
  "data": {
    "file_id": "uuid",
    "file_name": "contract.pdf",
    "url": "/tmp/uuid_contract.pdf",
    "size_bytes": 102400
  }
}
```

#### 3.2 获取附件列表
```
GET /attachments
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "uuid",
      "file_name": "contract.pdf",
      "content_type": "application/pdf",
      "size_bytes": 102400,
      "storage_url": "/tmp/uuid_contract.pdf",
      "created_at": "2024-11-02 10:00:00"
    }
  ]
}
```

### 4. 模板和文档模块 (Templates & Documents)

#### 4.1 获取模板列表
```
GET /templates
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "tpl-001",
      "name": "劳动仲裁申请书",
      "description": "用于提交劳动仲裁申请的标准模板",
      "category": "仲裁",
      "fields": "[\"applicant_name\",\"applicant_gender\",...]",
      "created_at": "2024-11-02 10:00:00"
    }
  ]
}
```

#### 4.2 获取模板详情
```
GET /templates/{template_id}
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": {
    "id": "tpl-001",
    "name": "劳动仲裁申请书",
    "description": "用于提交劳动仲裁申请的标准模板",
    "category": "仲裁",
    "content": "劳动仲裁申请书\n\n申请人：{applicant_name}...",
    "fields": ["applicant_name", "applicant_gender", "applicant_id", ...],
    "created_at": "2024-11-02 10:00:00"
  }
}
```

#### 4.3 创建模板
```
POST /templates
```

**需要认证**: 是

**请求体**:
```json
{
  "name": "新模板",
  "description": "模板描述",
  "category": "分类",
  "content": "模板内容 {field1} {field2}",
  "fields": ["field1", "field2"]
}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "name": "新模板"
  }
}
```

#### 4.4 生成文档
```
POST /documents
```

**需要认证**: 是

**请求体**:
```json
{
  "template_id": "tpl-001",
  "title": "我的仲裁申请书",
  "data": {
    "applicant_name": "张三",
    "applicant_gender": "男",
    "applicant_id": "110101199001011234",
    "applicant_phone": "13800000000",
    ...
  }
}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "title": "我的仲裁申请书",
    "content": "劳动仲裁申请书\n\n申请人：张三\n性别：男...",
    "status": "completed"
  }
}
```

#### 4.5 获取文档列表
```
GET /documents
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "template_id": "tpl-001",
      "title": "我的仲裁申请书",
      "content": "...",
      "status": "completed",
      "created_at": "2024-11-02 10:00:00"
    }
  ]
}
```

#### 4.6 获取文档详情
```
GET /documents/{doc_id}
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "template_id": "tpl-001",
    "title": "我的仲裁申请书",
    "content": "劳动仲裁申请书\n\n申请人：张三...",
    "status": "completed",
    "created_at": "2024-11-02 10:00:00"
  }
}
```

### 5. 订单和支付模块 (Orders & Payment)

#### 5.1 创建订单
```
POST /orders/create
```

**需要认证**: 是

**请求体**:
```json
{
  "product_type": "consultation",
  "product_id": "optional_product_id",
  "amount": 99.00,
  "payment_method": "wechat"
}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "order_id": "uuid",
    "amount": 99.00,
    "status": "pending",
    "payment_url": "https://mock-payment.example.com/pay?order_id=...",
    "qr_code": "data:image/png;base64,..."
  }
}
```

#### 5.2 模拟支付
```
POST /orders/{order_id}/pay
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": {
    "order_id": "uuid",
    "status": "paid",
    "transaction_id": "TXN-XXXXXXXXXXXXXXXX",
    "paid_at": "2024-11-02T10:00:00"
  }
}
```

#### 5.3 获取订单列表
```
GET /orders
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "product_type": "consultation",
      "product_id": null,
      "amount": 99.00,
      "status": "paid",
      "payment_method": "wechat",
      "transaction_id": "TXN-XXX",
      "created_at": "2024-11-02 10:00:00",
      "paid_at": "2024-11-02 10:01:00"
    }
  ]
}
```

#### 5.4 获取订单详情
```
GET /orders/{order_id}
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "product_type": "consultation",
    "amount": 99.00,
    "status": "paid",
    "payment_method": "wechat",
    "transaction_id": "TXN-XXX",
    "created_at": "2024-11-02 10:00:00",
    "paid_at": "2024-11-02 10:01:00"
  }
}
```

### 6. 管理后台模块 (Admin)

#### 6.1 获取用户列表
```
GET /admin/users
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "uuid",
      "phone": "13800000000",
      "name": "User-13800000000",
      "created_at": "2024-11-02 10:00:00"
    }
  ]
}
```

#### 6.2 获取会话列表（含用户信息）
```
GET /admin/conversations
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "title": "咨询工资纠纷",
      "phone": "13800000000",
      "user_name": "User-13800000000",
      "created_at": "2024-11-02 10:00:00"
    }
  ]
}
```

#### 6.3 获取订单列表（含用户信息）
```
GET /admin/orders
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "product_type": "consultation",
      "amount": 99.00,
      "status": "paid",
      "phone": "13800000000",
      "user_name": "User-13800000000",
      "created_at": "2024-11-02 10:00:00",
      "paid_at": "2024-11-02 10:01:00"
    }
  ]
}
```

#### 6.4 获取统计数据
```
GET /admin/stats
```

**需要认证**: 是

**响应**:
```json
{
  "code": 0,
  "data": {
    "total_users": 100,
    "total_conversations": 250,
    "total_messages": 1500,
    "paid_orders": 80,
    "total_revenue": 7920.00
  }
}
```

### 7. 系统模块

#### 7.1 健康检查
```
GET /health
```

**需要认证**: 否

**响应**:
```json
{
  "code": 0,
  "message": "SalaryHelper API is running"
}
```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（token无效或过期） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 预置模板说明

系统预置了3个文书模板：

### 1. 劳动仲裁申请书 (tpl-001)
**必填字段**:
- applicant_name - 申请人姓名
- applicant_gender - 申请人性别
- applicant_id - 申请人身份证号
- applicant_phone - 申请人联系电话
- applicant_address - 申请人住址
- respondent_name - 被申请人名称
- respondent_legal_rep - 被申请人法定代表人
- respondent_address - 被申请人地址
- respondent_phone - 被申请人联系电话
- arbitration_requests - 仲裁请求
- facts_and_reasons - 事实与理由
- evidence_list - 证据材料清单
- arbitration_committee - 仲裁委员会名称
- application_date - 申请日期

### 2. 工资支付申诉书 (tpl-002)
**必填字段**:
- complainant_name - 申诉人姓名
- complainant_id - 申诉人身份证号
- complainant_contact - 申诉人联系方式
- company_name - 公司名称
- company_code - 公司统一社会信用代码
- company_address - 公司地址
- employment_start - 入职日期
- employment_end - 离职日期
- position - 岗位
- amount - 拖欠金额
- wage_details - 工资明细
- evidence_list - 证据清单
- requests - 诉求
- date - 日期

### 3. 劳动合同解除通知书 (tpl-003)
**必填字段**:
- employee_name - 员工姓名
- article_number - 法律条款编号
- termination_reason - 解除原因
- termination_date - 解除日期
- detailed_reason - 详细理由
- compensation_details - 补偿说明
- handover_date - 交接截止日期
- company_name - 公司名称
- notice_date - 通知日期

## 使用示例

### Python示例
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 登录
response = requests.post(f"{BASE_URL}/auth/login", json={
    "phone": "13800000000",
    "code": "123456"
})
token = response.json()['data']['token']

# 使用token访问API
headers = {"Authorization": f"Bearer {token}"}

# 创建会话
response = requests.post(f"{BASE_URL}/conversations", 
                        json={"title": "咨询工资问题"}, 
                        headers=headers)

# 生成文档
response = requests.post(f"{BASE_URL}/documents",
                        json={
                            "template_id": "tpl-001",
                            "title": "我的仲裁申请",
                            "data": {...}
                        },
                        headers=headers)
```

### JavaScript示例
```javascript
const BASE_URL = "http://localhost:8000/api/v1";

// 登录
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({phone: "13800000000", code: "123456"})
});
const {data: {token}} = await loginResponse.json();

// 使用token访问API
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// 创建订单
const orderResponse = await fetch(`${BASE_URL}/orders/create`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    product_type: "consultation",
    amount: 99.00,
    payment_method: "wechat"
  })
});
```
