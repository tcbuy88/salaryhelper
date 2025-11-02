# 支付接入指南（微信 H5 与 支付宝 WAP）

目标：可靠地完成用户下单并获取支付回调，确保验签与幂等性。

准备与商户资料
- 企业营业执照、法人身份证、银行结算信息
- 微信商户号（MchID），API Key（或 API v3）
- 支付宝 AppID、商户私钥、支付宝公钥
- 回调域名需为 HTTPS，有效证书；联调可用 ngrok 暴露

后端要点
1. 订单创建（POST /api/v1/orders/create）
   - 校验 sku、创建 order（status=created）
   - 构造下单请求（微信 unifiedorder -> mweb_url；支付宝 wap -> form/url）
   - 保存 provider 返回的 trade_id/prepay_id 并返回 pay_info 给前端

2. 回调验签（/api/v1/payments/callback/{provider}）
   - 验证签名（微信用 API Key / v3 验签；支付宝用公钥）
   - 检查金额、order id 一致
   - 幂等更新（若订单已 paid 则忽略重复回调）
   - 返回 provider 要求的固定响应（微信返回 XML 成功 / 支付宝返回 200 OK）

3. 发放权益
   - 更新用户状态（开通会员 / 增加次数 / 增加余额）
   - 记录 payment logs、原始回调体用于对账

安全与容错
- 严格验签并记录回调原始体
- 幂等 key（order_out_no）防止重复发放
- 审计日志与报警（异常金额、异常频繁回调）

联调建议
- 使用沙箱/测试商户进行 E2E
- 用 Postman 或脚本模拟回调，验证服务器端验签逻辑
- 在本地用 ngrok 暴露 notify_url 供支付平台回调
