# 下一步（短期联调清单）

1. 在本地启动 Mock：
   - 使用 Prism： prism mock openapi.yaml -p 4000
   - 或运行 docker compose -f docker-compose-full.yml up --build

2. 替换前端 DEMO：
   - 把 index.html 中的 <script src="app.js"> 替换为
     <script src="/api-client.js"></script>
     <script src="/app-real.js"></script>

3. 启动后端 stub（可选）：
   - cd server && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000

4. 联调核心流程：
   - 登录 -> 创建会话 -> 发送消息 -> 等待 AI 回复 -> 文书生成 -> 下单支付 -> 回调验签

5. 支付联调：
   - 准备微信/支付宝沙箱商户号，设置 notify_url（可用 ngrok 暴露）

6. 完成文档补全与法务确认：
   - 确认隐私与录音同意文案
   - 确认数据保留策略（证据保留年限）

7. 上线前检查：
   - 自动化测试覆盖率、渗透测试、支付 & 回调验签测试、监控告警
