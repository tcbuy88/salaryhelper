# UI 设计规范（SalaryHelper）

版本：v1（移动优先 H5 + 管理台 Desktop）

概述
- 目标用户：劳动者、HR 顾问、法务人员
- 设备优先级：移动（375px - 420px 视口）为主，管理台 Desktop（≥1024px）为辅
- 设计方向：可信、沉稳、简洁、以信息可读性与流程低摩擦为核心

色彩（建议）
- 主色 Primary: #1866FF（交互主色）
- 辅色 Accent: #00B08B（成功/提醒）
- 文本主色: #1F2D3D
- 次级文本: #6B7280
- 背景: #F6F8FB（页面背景）；卡片：#FFFFFF
- 错误: #E53935；警告: #F59E0B

排版
- 字体：系统字体优先；中文：思源宋体/自定义；Fallback：Helvetica, Arial, sans-serif
- 标题/文案：
  - H1: 24px / 600
  - H2: 20px / 600
  - 基本正文：14px / 400
  - 辅助文字：12px / 400
- 行高：1.4 - 1.6

栅格与间距
- 移动端：12px 基础间距（8/12/16/24/32）
- 管理台：布局使用 12 列栅格，间距 16/24/32

图标与按钮
- 图标：使用 20/24px 常用图标集（SVG）
- 主按钮（Primary）：背景主色，白字，圆角 8px
- 次按钮（Secondary）：边框主色/浅背景

卡片设计
- 圆角 8px，阴影轻微（box-shadow: 0 1px 4px rgba(31,45,61,0.06)）
- 卡片内间距 12-16px

组件库（高层）
- Button、IconButton、Card、Modal、AppHeader、BottomNav、Tabs、FormField（输入、选择、日期）、Uploader、Table（Admin）

表单与校验
- 输入需即时校验并给出可读错误提示（红色文本与图标）
- 必填项用 * 标识，长度/格式限制在 placeholder 下显示提示

可访问性（A11y）
- 对比度符合 WCAG AA（文本与背景最小比率 4.5:1）
- 所有交互可通过键盘操作
- 图片/图标提供 aria-label 或 alt 文本
- 表单字段具备 label 与 aria-describedby 关联错误节点

响应式与断点
- 移动：≤ 420px
- 平板：421px - 1023px
- Desktop：≥ 1024px
- SPA 使用 history fallback（/index.html）

交互与微动效
- 点击/悬停有 100-200ms 反馈，避免过度动画
- 弹窗/模态使用淡入（opacity）和轻微 scale

示例页面/模块（概要）
- 首页（问题搜索 + 热门场景）
- 会话页（ChatList, ChatView, MessageInput）
- 文书生成（模板选择、动态表单、预览、导出）
- 我的（钱包、订单、登录）
- Admin（用户、订单、会话、模板管理）
