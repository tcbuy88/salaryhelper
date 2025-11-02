# 组件清单（前端开发用）  

说明：面向 Vue3 + TS 或 React + TS 实现。每个组件含 props / state / events / 依赖 API。

目录
- 公共组件
  - AppHeader
  - BottomNav
  - Modal
  - IconButton
  - Card
- 会话相关
  - ChatListPage
  - ChatItem
  - ChatViewPage
  - MessageBubble
  - MessageList
  - MessageInput
  - AttachUploader
  - ConversationExportButton
- 文书/模板
  - DocGeneratorPage
  - TemplateSelector
  - DocForm (dynamic)
  - DocPreview
- 我的/支付
  - MePage
  - LoginModal
  - WalletCard
  - RechargeModal
  - OrdersList
- Admin 管理台
  - AdminLayout
  - AdminSidebar
  - DashboardPage
  - UsersTable
  - TemplatesManager
  - OrdersTable

示例组件定义（核心，供开发直接实现）

1) AppHeader
- props:
  - title: string
  - showBack?: boolean
  - actions?: Array<{ icon:string, onClick:() => void }>
- events:
  - onBack()

2) MessageBubble
- props:
  - message: { id, sender, content, attachments?, created_at }
  - isOwn: boolean
- state: none
- render: 支持 markdown 基本格式、代码块、引用、附件链接

3) MessageInput
- props:
  - disabled?: boolean
  - placeholder?: string
- state:
  - text: string
  - files: File[]
- events:
  - onSend({ text, files })
  - onAttach(File)
- behavior:
  - 支持 Enter 发送（组合键换行），上传附件调 AttachUploader

4) AttachUploader
- props:
  - accept?: string
  - maxSizeMB?: number
- events:
  - onUploaded(fileMeta)
- API:
  - POST /api/v1/upload -> { file_id, url, hash }

5) DocForm (dynamic)
- props:
  - schema: JSONSchema
  - initialValues?: {}
- events:
  - onChange(values)
  - onSubmit(values)
- render:
  - 根据 schema 动态渲染输入/选择/日期/textarea

数据模型（示例 Typescript 接口）
- Conversation { id:string, title:string, last?:string, tags?:string[], created_at:string }
- Message { id:string, conversation_id:string, sender:'user'|'ai'|'operator', content:string, attachments?: FileMeta[], token_cost?: number, created_at:string }
- Template { id:string, name:string, type:string, region?:string, fields: JSONSchema, content_template?: string }

实现建议
- 先实现最小可交付组件：MessageBubble, MessageList, MessageInput, AttachUploader, DocForm, DocPreview
- 使用 TypeScript interface 与 API client（统一封装请求和错误处理）
- 所有组件尽量无副作用，交互由页面层管理状态（或 Pinia/Redux）
