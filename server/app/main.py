from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid, os, shutil, sqlite3, json
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

app = FastAPI(title="SalaryHelper API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = "/tmp/salaryhelper_uploads"
DATABASE_URL = "/tmp/salaryhelper.db"
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database setup
def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        phone TEXT UNIQUE NOT NULL,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Conversations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        sender TEXT NOT NULL,
        sender_id TEXT,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    )
    """)
    
    # Attachments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attachments (
        id TEXT PRIMARY KEY,
        file_name TEXT NOT NULL,
        content_type TEXT,
        size_bytes INTEGER,
        storage_url TEXT,
        preview_url TEXT,
        metadata TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Templates table for document generation
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT,
        content TEXT NOT NULL,
        fields TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Documents table for generated documents
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        template_id TEXT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (template_id) REFERENCES templates (id)
    )
    """)
    
    # Orders table for payment system
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        product_type TEXT NOT NULL,
        product_id TEXT,
        amount REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        payment_method TEXT,
        transaction_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        paid_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Insert default templates
    cursor.execute("SELECT COUNT(*) FROM templates")
    count = cursor.fetchone()[0]
    if count == 0:
        default_templates = [
            (
                "tpl-001",
                "劳动仲裁申请书",
                "用于提交劳动仲裁申请的标准模板",
                "仲裁",
                """劳动仲裁申请书

申请人：{applicant_name}
性别：{applicant_gender}
身份证号：{applicant_id}
联系电话：{applicant_phone}
住址：{applicant_address}

被申请人：{respondent_name}
法定代表人：{respondent_legal_rep}
地址：{respondent_address}
联系电话：{respondent_phone}

仲裁请求：
{arbitration_requests}

事实与理由：
{facts_and_reasons}

证据材料清单：
{evidence_list}

此致
{arbitration_committee}

申请人：{applicant_name}
日期：{application_date}""",
                '["applicant_name","applicant_gender","applicant_id","applicant_phone","applicant_address","respondent_name","respondent_legal_rep","respondent_address","respondent_phone","arbitration_requests","facts_and_reasons","evidence_list","arbitration_committee","application_date"]'
            ),
            (
                "tpl-002",
                "工资支付申诉书",
                "用于申诉拖欠工资问题",
                "工资",
                """工资支付申诉书

申诉人：{complainant_name}
身份证号：{complainant_id}
联系方式：{complainant_contact}

被申诉人：{company_name}
统一社会信用代码：{company_code}
联系地址：{company_address}

申诉事项：
本人于{employment_start}至{employment_end}期间在被申诉人处工作，岗位为{position}。
被申诉人拖欠本人工资共计人民币{amount}元，具体如下：
{wage_details}

证据：
{evidence_list}

请求：
{requests}

申诉人：{complainant_name}
日期：{date}""",
                '["complainant_name","complainant_id","complainant_contact","company_name","company_code","company_address","employment_start","employment_end","position","amount","wage_details","evidence_list","requests","date"]'
            ),
            (
                "tpl-003",
                "劳动合同解除通知书",
                "用于通知解除劳动合同",
                "合同",
                """劳动合同解除通知书

{employee_name}：

根据《劳动合同法》第{article_number}条规定，因{termination_reason}，公司决定于{termination_date}与您解除劳动合同。

解除理由详述：
{detailed_reason}

补偿说明：
{compensation_details}

请您于{handover_date}前办理工作交接手续。

特此通知。

{company_name}
日期：{notice_date}""",
                '["employee_name","article_number","termination_reason","termination_date","detailed_reason","compensation_details","handover_date","company_name","notice_date"]'
            )
        ]
        
        for template_data in default_templates:
            cursor.execute(
                "INSERT INTO templates (id, name, description, category, content, fields) VALUES (?, ?, ?, ?, ?, ?)",
                template_data
            )
    
    conn.commit()
    conn.close()

# Pydantic models
class LoginRequest(BaseModel):
    phone: str
    code: str

class TokenResponse(BaseModel):
    code: int
    data: Dict[str, Any]

class User(BaseModel):
    id: str
    phone: str
    name: Optional[str] = None

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class MessageCreate(BaseModel):
    text: Optional[str] = None
    content: Optional[str] = None

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    content: str
    fields: Optional[List[str]] = None

class DocumentCreate(BaseModel):
    template_id: str
    title: Optional[str] = None
    data: Dict[str, str]

class OrderCreate(BaseModel):
    product_type: str
    product_id: Optional[str] = None
    amount: float
    payment_method: Optional[str] = "wechat"

# JWT functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Database helpers
def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Auth endpoints
@app.post("/api/v1/auth/send-sms")
async def send_sms(payload: dict):
    phone = payload.get("phone")
    # Mock SMS sending - always return success with code 123456
    return {"code": 0, "message": "验证码已发送", "data": {"code": "123456"}}

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    # Mock verification - accept any phone with code 123456
    if request.code != "123456":
        raise HTTPException(status_code=400, detail="验证码错误")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get or create user
    cursor.execute("SELECT * FROM users WHERE phone = ?", (request.phone,))
    user = cursor.fetchone()
    
    if not user:
        user_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO users (id, phone, name) VALUES (?, ?, ?)",
            (user_id, request.phone, f"User-{request.phone}")
        )
        user_data = {"id": user_id, "phone": request.phone, "name": f"User-{request.phone}"}
    else:
        user_data = dict(user)
    
    conn.commit()
    conn.close()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data["id"]}, expires_delta=access_token_expires
    )
    
    return {
        "code": 0,
        "data": {
            "token": access_token,
            "user": user_data
        }
    }

@app.get("/api/v1/auth/me")
async def get_current_user(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"code": 0, "data": dict(user)}

# Conversation endpoints
@app.post("/api/v1/conversations")
async def create_conversation(conversation: ConversationCreate, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    conv_id = str(uuid.uuid4())
    title = conversation.title or f"会话-{datetime.now().strftime('%m%d %H%M')}"
    
    cursor.execute(
        "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
        (conv_id, user_id, title)
    )
    
    conn.commit()
    conn.close()
    
    return {"code": 0, "data": {"id": conv_id, "title": title}}

@app.get("/api/v1/conversations")
async def list_conversations(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM conversations WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    conversations = cursor.fetchall()
    conn.close()
    
    return {"code": 0, "data": [dict(conv) for conv in conversations]}

@app.get("/api/v1/conversations/{convId}")
async def get_conversation(convId: str, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify conversation belongs to user
    cursor.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (convId, user_id))
    conversation = cursor.fetchone()
    
    if not conversation:
        conn.close()
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # Get messages
    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (convId,)
    )
    messages = cursor.fetchall()
    conn.close()
    
    return {
        "code": 0,
        "data": {
            "conversation": dict(conversation),
            "messages": [dict(msg) for msg in messages]
        }
    }

@app.post("/api/v1/conversations/{convId}/messages")
async def post_message(convId: str, message: MessageCreate, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify conversation belongs to user
    cursor.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (convId, user_id))
    conversation = cursor.fetchone()
    
    if not conversation:
        conn.close()
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # Create user message
    message_id = str(uuid.uuid4())
    content = message.text or message.content or ""
    
    cursor.execute(
        "INSERT INTO messages (id, conversation_id, sender, sender_id, content) VALUES (?, ?, ?, ?, ?)",
        (message_id, convId, "user", user_id, content)
    )
    
    conn.commit()
    
    # Mock AI response (simplified - in real app, this would call AI service)
    ai_message_id = str(uuid.uuid4())
    ai_response = f"（模拟回复）已收到您的消息：{content}"
    
    cursor.execute(
        "INSERT INTO messages (id, conversation_id, sender, content) VALUES (?, ?, ?, ?)",
        (ai_message_id, convId, "ai", ai_response)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "code": 0,
        "data": {
            "message_id": message_id,
            "status": "sent",
            "ai_reply": {
                "message_id": ai_message_id,
                "content": ai_response
            }
        }
    }

@app.post("/api/v1/upload")
async def upload(file: UploadFile = File(...), user_id: str = Depends(verify_token)):
    file_id = str(uuid.uuid4())
    dest = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    # Save file
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Save to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO attachments 
           (id, file_name, content_type, size_bytes, storage_url) 
           VALUES (?, ?, ?, ?, ?)""",
        (file_id, file.filename, file.content_type, os.path.getsize(dest), dest)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "code": 0,
        "data": {
            "file_id": file_id,
            "file_name": file.filename,
            "url": f"/tmp/{file_id}_{file.filename}",
            "size_bytes": os.path.getsize(dest)
        }
    }

@app.get("/api/v1/attachments")
async def list_attachments(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM attachments ORDER BY created_at DESC")
    attachments = cursor.fetchall()
    conn.close()
    
    return {"code": 0, "data": [dict(att) for att in attachments]}

# Template endpoints
@app.get("/api/v1/templates")
async def list_templates(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM templates ORDER BY created_at DESC")
    templates = cursor.fetchall()
    conn.close()
    
    return {"code": 0, "data": [dict(tpl) for tpl in templates]}

@app.get("/api/v1/templates/{template_id}")
async def get_template(template_id: str, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
    template = cursor.fetchone()
    conn.close()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    template_dict = dict(template)
    if template_dict.get("fields"):
        template_dict["fields"] = json.loads(template_dict["fields"])
    
    return {"code": 0, "data": template_dict}

@app.post("/api/v1/templates")
async def create_template(template: TemplateCreate, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    template_id = str(uuid.uuid4())
    fields_json = json.dumps(template.fields) if template.fields else None
    
    cursor.execute(
        "INSERT INTO templates (id, name, description, category, content, fields) VALUES (?, ?, ?, ?, ?, ?)",
        (template_id, template.name, template.description, template.category, template.content, fields_json)
    )
    
    conn.commit()
    conn.close()
    
    return {"code": 0, "data": {"id": template_id, "name": template.name}}

# Document generation endpoints
@app.post("/api/v1/documents")
async def create_document(doc: DocumentCreate, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get template
    cursor.execute("SELECT * FROM templates WHERE id = ?", (doc.template_id,))
    template = cursor.fetchone()
    
    if not template:
        conn.close()
        raise HTTPException(status_code=404, detail="模板不存在")
    
    template_dict = dict(template)
    
    # Fill template with data
    try:
        content = template_dict["content"].format(**doc.data)
    except KeyError as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"缺少必填字段: {str(e)}")
    
    # Create document
    doc_id = str(uuid.uuid4())
    title = doc.title or template_dict["name"]
    
    cursor.execute(
        "INSERT INTO documents (id, user_id, template_id, title, content, status) VALUES (?, ?, ?, ?, ?, ?)",
        (doc_id, user_id, doc.template_id, title, content, "completed")
    )
    
    conn.commit()
    conn.close()
    
    return {
        "code": 0,
        "data": {
            "id": doc_id,
            "title": title,
            "content": content,
            "status": "completed"
        }
    }

@app.get("/api/v1/documents")
async def list_documents(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    documents = cursor.fetchall()
    conn.close()
    
    return {"code": 0, "data": [dict(doc) for doc in documents]}

@app.get("/api/v1/documents/{doc_id}")
async def get_document(doc_id: str, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id))
    document = cursor.fetchone()
    conn.close()
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return {"code": 0, "data": dict(document)}

# Order and Payment endpoints
@app.post("/api/v1/orders/create")
async def create_order(order: OrderCreate, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    order_id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO orders (id, user_id, product_type, product_id, amount, status, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (order_id, user_id, order.product_type, order.product_id, order.amount, "pending", order.payment_method)
    )
    
    conn.commit()
    conn.close()
    
    # Mock payment URL/QR code
    payment_url = f"https://mock-payment.example.com/pay?order_id={order_id}&amount={order.amount}"
    
    return {
        "code": 0,
        "data": {
            "order_id": order_id,
            "amount": order.amount,
            "status": "pending",
            "payment_url": payment_url,
            "qr_code": f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        }
    }

@app.post("/api/v1/orders/{order_id}/pay")
async def simulate_payment(order_id: str, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify order belongs to user
    cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # Simulate successful payment
    transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"
    
    cursor.execute(
        "UPDATE orders SET status = ?, transaction_id = ?, paid_at = ? WHERE id = ?",
        ("paid", transaction_id, datetime.now(), order_id)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "code": 0,
        "data": {
            "order_id": order_id,
            "status": "paid",
            "transaction_id": transaction_id,
            "paid_at": datetime.now().isoformat()
        }
    }

@app.get("/api/v1/orders")
async def list_orders(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    orders = cursor.fetchall()
    conn.close()
    
    return {"code": 0, "data": [dict(order) for order in orders]}

@app.get("/api/v1/orders/{order_id}")
async def get_order(order_id: str, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
    order = cursor.fetchone()
    conn.close()
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    return {"code": 0, "data": dict(order)}

# Admin endpoints
@app.get("/api/v1/admin/users")
async def admin_list_users(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    
    return {"code": 0, "data": [dict(user) for user in users]}

@app.get("/api/v1/admin/conversations")
async def admin_list_conversations(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, u.phone, u.name as user_name
        FROM conversations c
        LEFT JOIN users u ON c.user_id = u.id
        ORDER BY c.created_at DESC
    """)
    conversations = cursor.fetchall()
    conn.close()
    
    return {"code": 0, "data": [dict(conv) for conv in conversations]}

@app.get("/api/v1/admin/orders")
async def admin_list_orders(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT o.*, u.phone, u.name as user_name
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """)
    orders = cursor.fetchall()
    conn.close()
    
    return {"code": 0, "data": [dict(order) for order in orders]}

@app.get("/api/v1/admin/stats")
async def admin_get_stats(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get various statistics
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM conversations")
    total_conversations = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid'")
    paid_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(amount) FROM orders WHERE status = 'paid'")
    total_revenue = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "code": 0,
        "data": {
            "total_users": total_users,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "paid_orders": paid_orders,
            "total_revenue": total_revenue
        }
    }

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    return {"code": 0, "message": "SalaryHelper API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
