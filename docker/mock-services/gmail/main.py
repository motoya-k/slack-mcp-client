from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gmail MCP Mock Service",
    description="Gmail API用のモックサービス",
    version="0.1.0",
)

# メールデータを保存するインメモリデータベース
emails_db = {}


class EmailAttachment(BaseModel):
    filename: str
    content_type: str
    content: str


class Email(BaseModel):
    id: Optional[str] = None
    to: List[EmailStr]
    subject: str
    body: str
    from_email: EmailStr = "user@example.com"
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    attachments: Optional[List[EmailAttachment]] = None
    timestamp: Optional[datetime] = None


@app.get("/")
async def root():
    """
    ルートエンドポイント - ヘルスチェック用
    """
    return {"status": "ok", "service": "Gmail MCP Mock Service"}


@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {"status": "healthy"}


@app.post("/send_email", response_model=Dict[str, str])
async def send_email(email: Email):
    """
    メールを送信（モック）
    """
    logger.info(f"Sending email to {email.to} with subject: {email.subject}")

    # メールIDの生成
    email_id = str(uuid.uuid4())
    email.id = email_id
    email.timestamp = datetime.now()

    # メールの保存
    emails_db[email_id] = email.dict()

    return {"message_id": email_id, "status": "sent"}


@app.get("/get_emails", response_model=List[Email])
async def get_emails(
    max_results: int = Query(10, description="取得する最大件数"),
    query: Optional[str] = Query(None, description="検索クエリ"),
):
    """
    メールを取得（モック）
    """
    logger.info(f"Getting emails with query: {query}, max_results: {max_results}")

    # メールのフィルタリング
    filtered_emails = list(emails_db.values())

    if query:
        filtered_emails = [
            email
            for email in filtered_emails
            if query.lower() in email["subject"].lower()
            or query.lower() in email["body"].lower()
        ]

    # 最大件数で制限
    filtered_emails = filtered_emails[:max_results]

    return filtered_emails


@app.get("/get_email/{email_id}", response_model=Email)
async def get_email(email_id: str):
    """
    特定のメールを取得（モック）
    """
    logger.info(f"Getting email with ID: {email_id}")

    if email_id not in emails_db:
        raise HTTPException(status_code=404, detail="Email not found")

    return emails_db[email_id]


@app.delete("/delete_email/{email_id}", response_model=Dict[str, str])
async def delete_email(email_id: str):
    """
    メールを削除（モック）
    """
    logger.info(f"Deleting email with ID: {email_id}")

    if email_id not in emails_db:
        raise HTTPException(status_code=404, detail="Email not found")

    del emails_db[email_id]

    return {"status": "deleted", "email_id": email_id}


@app.get("/mcp/operations", response_model=Dict[str, List[str]])
async def get_operations():
    """
    サポートされているMCP操作を取得
    """
    return {"operations": ["send_email", "get_emails", "get_email", "delete_email"]}


@app.post("/mcp/execute", response_model=Dict[str, Any])
async def execute_operation(operation: Dict[str, Any] = Body(...)):
    """
    MCP操作を実行
    """
    operation_name = operation.get("operation")
    params = operation.get("params", {})

    logger.info(f"Executing MCP operation: {operation_name}")

    if operation_name == "send_email":
        email = Email(**params)
        result = await send_email(email)
        return {"status": "success", "data": result}

    elif operation_name == "get_emails":
        max_results = params.get("max_results", 10)
        query = params.get("query")
        result = await get_emails(max_results, query)
        return {"status": "success", "data": result}

    elif operation_name == "get_email":
        email_id = params.get("email_id")
        if not email_id:
            raise HTTPException(status_code=400, detail="email_id is required")
        result = await get_email(email_id)
        return {"status": "success", "data": result}

    elif operation_name == "delete_email":
        email_id = params.get("email_id")
        if not email_id:
            raise HTTPException(status_code=400, detail="email_id is required")
        result = await delete_email(email_id)
        return {"status": "success", "data": result}

    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown operation: {operation_name}"
        )
