from fastapi import FastAPI, UploadFile, File, HTTPException
import uuid, os, shutil
app = FastAPI()
UPLOAD_DIR = "/tmp/salaryhelper_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/v1/auth/send-sms")
async def send_sms(payload: dict):
    return {"code":0,"message":"ok"}

@app.post("/api/v1/auth/login")
async def login(payload: dict):
    user_id = str(uuid.uuid4())
    token = "demo-token-"+user_id
    return {"code":0,"data":{"token": token, "user": {"id": user_id, "phone": payload.get("phone")}}}

@app.post("/api/v1/upload")
async def upload(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    dest = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"code":0,"data":{"file_id": file_id, "url": f"/api/v1/uploads/{file_id}", "hash":"stub"}}

@app.get("/api/v1/uploads/{file_id}")
async def get_upload(file_id: str):
    for fn in os.listdir(UPLOAD_DIR):
        if fn.startswith(file_id + "_"):
            return {"code":0, "url": f"/tmp/{fn}"}
    raise HTTPException(status_code=404, detail="not found")

@app.post("/api/v1/conversations")
async def create_conversation(payload: dict):
    conv_id = str(uuid.uuid4())
    return {"code":0,"data":{"id": conv_id, "title": payload.get("title", "会话")}}

@app.post("/api/v1/conversations/{convId}/messages")
async def post_message(convId: str, payload: dict):
    # immediate mock reply
    return {"code":0,"data":{"message_id": str(uuid.uuid4()), "status":"done","ai_reply":"（模拟回复）请收集证据并生成文书。"}}
