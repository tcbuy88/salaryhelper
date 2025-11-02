# DEMO -> 真实后端 API 映射（替换点一览）

说明：标出 DEMO 中需要替换的 mock 调用并对应真实 REST 接口（建议路径 /api/v1/*）。

Auth
- POST /api/v1/auth/send-sms
  - body: { phone }
  - resp: { code, message }
- POST /api/v1/auth/login
  - body: { phone, code }
  - resp: { code, data:{ token, refresh_token, user } }

Upload
- POST /api/v1/upload (multipart/form-data file)
  - resp: { code, data: { file_id, url, hash } }

Conversations & Messages
- GET /api/v1/conversations?limit=&cursor=
  - resp: { code, data: [Conversation] }
- POST /api/v1/conversations
  - body: { title?, tags? }
  - resp: { code, data: Conversation }
- GET /api/v1/conversations/{id}?limit=&cursor=
  - resp: { code, data: { conversation, messages: [] } }
- POST /api/v1/conversations/{id}/messages
  - body: { text, attachments: [file_id] }
  - resp: { code, data:{ message_id, status } }  // status: queued/done/error
- POST /api/v1/conversations/{id}/export
  - body: { format:'pdf'|'txt' }
  - resp: { code, data:{ file_url } }

Templates / DocGen
- GET /api/v1/templates?type=&region=
  - resp: { code, data: [Template] }
- POST /api/v1/templates/{id}/render
  - body: { values: {} }
  - resp: { code, data: { rendered_html, rendered_text, file_id } }

Orders / Payments
- POST /api/v1/orders/create
  - body: { sku_id, pay_method }
  - resp: { code, data: { order_id, amount, pay_info } }
- POST /api/v1/payments/callback/{provider}
  - provider: wx | alipay
  - server validates signature and updates order

Admin (示例)
- GET /api/v1/admin/metrics
- GET /api/v1/admin/users
- GET /api/v1/admin/conversations
- GET /api/v1/admin/orders

注意事项
- 所有接口统一返回 { code, message, data } 结构（OpenAPI 可指明更详细 schema）
- 敏感操作（上传身份证、删除证据）需二次确认与权限校验
