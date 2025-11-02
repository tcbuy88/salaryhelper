# AI 集成（RAG + Prompt 管控）执行说明

目标：在保证法律咨询可审计与可复核的前提下，用 RAG（检索增强生成）降低 hallucination 并给出来源引用。

架构概览
- 向量检索（Qdrant / Milvus / Weaviate / Elastic kNN）
- Embedding 服务（供应商或本地 open-source）
- RAG Orchestrator（后端 worker）
- Model Adapter（对接不同 LLM 供应商或本地模型）
- 审计数据库（保存 prompt、retrieved doc ids、full response、token_cost）

处理流程（消息到回复）
1. 接收用户消息（POST /conversations/{id}/messages）
2. 保存用户消息并入队（status = queued）
3. Worker 从队列拉取：
   - 调用 /internal/search(q, topk)
   - 构建 Prompt（system + retrieved docs + instruction + user message）
   - 调用 model.complete（可选 streaming）
   - 后处理并存入 messages (sender=ai)，记录 token_cost 和引用 docs
   - 若触发复核规则，标注 conversation pending_review 并通知 Admin

Prompt 管控（示例）
- System prompt 指令（固定）:
  "你是劳动法咨询助手。回答必须：1) 简明结论；2) 相关法律条款/来源；3) 三步可执行建议；4) 免责声明：非律师意见。"
- 把检索结果以摘要 + citation 放前面，并限制引用长度

检索策略
- 文档预处理：
  - 文本清洗、分段（chunk size ~ 500-1000 tokens），metadata 包含来源/日期/地区
- 向量索引：
  - 支持根据 region/area filter
  - topk 初始 6，视情况调整
- fallback：若检索返回空，降低检索权重并在 prompt 中加入“可用外部法规未找到”提示

人工复核触发规则（示例）
- 预估赔偿金额 > configurable_threshold（比如 ¥100k）
- 用户请求“律师代理”或“起诉代理”
- 生成内容置信度低或存在相互矛盾（可基于模型返回的置信度/评分）
- 模型回答含法律结论但缺乏明确来源

审计与保存
- 必须保存：原始 prompt、检索到的 doc ids、模型输出、token counts、时间戳与 worker id
- 存储：结构化日志、ELK 或 object storage（大文本）

模型与供应商建议（大陆可用）
- 首选：国内供应商（文心、讯飞、阿里、百度）以减少网络与合规问题
- 可选：本地部署开源模型（Llama 2 / Mistral / Baichuan）+ 加速（GPU / Triton）
- 结合多模型 A/B 或 fallback 逻辑（primary -> secondary）

成本控制
- 每次调用记录 token_cost，按 SKU 收费或扣减用户余额
- 限流：非会员每日免费 n 次，会员增加次数或不限

部署建议
- Worker 与向量库分离，可水平扩容
- 定期 snapshot 向量库并备份
