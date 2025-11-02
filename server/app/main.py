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

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    return {"code": 0, "message": "SalaryHelper API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
