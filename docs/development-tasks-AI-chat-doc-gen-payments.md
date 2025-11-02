# 开发任务拆解（AI Chat / DocGen / Payments） — 推荐优先级与估时

说明：把任务分解为前端、后端、AI（Worker）与运维/测试项。

高优先级（必须）
1. Auth（2d）
   - 后端：/auth/send-sms, /auth/login, token 签发
   - 前端：LoginModal + token 存储/刷新

2. File Upload（2d）
   - 后端：/upload -> 存 OSS / 本地 stub
   - 前端：AttachUploader（进度、preview）

3. 会话基础（5d）
   - 后端：会话模型、消息模型、POST /conversations, GET /conversations/{id}
   - 前端：ChatListPage + ChatViewPage + MessageList

4. 发送消息 & Worker（6d）
   - 后端：POST /conversations/{id}/messages -> 入队
   - Worker：检索 -> prompt 构建 -> 调用模型 -> 回写消息
   - 前端：MessageInput + optimistic UI + poll 或 WebSocket

5. DocGen（5d）
   - 后端：模板 CRUD, /templates/{id}/render（服务端渲染）
   - 前端：TemplateSelector, DocForm, DocPreview

6. Orders & Payments（6d）
   - 后端：orders 创建、支付集成（微信/支付宝）、回调验签
   - 前端：RechargeModal -> create order -> 跳转支付

中优先级（可并行）
- Admin 功能（用户/订单/会话/模板列表） 4d
- Export 会话（txt/pdf） 2d
- 计费/限流/风控（免费额度、token 计数） 4d

低优先级（后期）
- 语音输入/转写 / 高级律师对接 / 分账完整流程

测试与 CI
- Mock server（OpenAPI + Prism）供前端并行开发
- 集成测试：回调验签、支付流程、worker end-to-end
- E2E：使用 Playwright / Cypress 做主流程测试

部署/运维
- Docker + docker-compose / Kubernetes
- 向量库（Qdrant/Milvus）独立部署
- Worker 使用 Redis Queue / Celery 或 Kubernetes Jobs
