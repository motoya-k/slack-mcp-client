from fastapi import FastAPI, HTTPException, Query, Body, Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import uuid
import logging
from datetime import datetime

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Notion MCP Mock Service",
    description="Notion API用のモックサービス",
    version="0.1.0",
)

# Notionデータを保存するインメモリデータベース
pages_db = {}
databases_db = {}


class RichText(BaseModel):
    content: str
    annotations: Optional[Dict[str, bool]] = None


class PageProperty(BaseModel):
    type: str
    value: Any


class PageContent(BaseModel):
    title: str
    properties: Dict[str, PageProperty] = {}
    content: Optional[List[Dict[str, Any]]] = None


class Page(BaseModel):
    id: Optional[str] = None
    parent_id: Optional[str] = None
    title: str
    properties: Dict[str, PageProperty] = {}
    content: Optional[List[Dict[str, Any]]] = None
    created_time: Optional[datetime] = None
    last_edited_time: Optional[datetime] = None


class Database(BaseModel):
    id: Optional[str] = None
    title: str
    properties: Dict[str, Dict[str, Any]] = {}
    created_time: Optional[datetime] = None
    last_edited_time: Optional[datetime] = None


@app.get("/")
async def root():
    """
    ルートエンドポイント - ヘルスチェック用
    """
    return {"status": "ok", "service": "Notion MCP Mock Service"}


@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {"status": "healthy"}


@app.post("/pages", response_model=Dict[str, Any])
async def create_page(page: Page):
    """
    ページを作成（モック）
    """
    logger.info(f"Creating page with title: {page.title}")

    # ページIDの生成
    page_id = str(uuid.uuid4())
    page.id = page_id
    page.created_time = datetime.now()
    page.last_edited_time = datetime.now()

    # ページの保存
    pages_db[page_id] = page.dict()

    return {
        "id": page_id,
        "object": "page",
        "created_time": page.created_time.isoformat(),
        "last_edited_time": page.last_edited_time.isoformat(),
        "title": page.title,
        "parent": (
            {"type": "page_id", "page_id": page.parent_id}
            if page.parent_id
            else {"type": "workspace", "workspace": True}
        ),
    }


@app.get("/pages/{page_id}", response_model=Dict[str, Any])
async def get_page(page_id: str):
    """
    ページを取得（モック）
    """
    logger.info(f"Getting page with ID: {page_id}")

    if page_id not in pages_db:
        raise HTTPException(status_code=404, detail="Page not found")

    page = pages_db[page_id]

    return {
        "id": page["id"],
        "object": "page",
        "created_time": (
            page["created_time"].isoformat()
            if isinstance(page["created_time"], datetime)
            else page["created_time"]
        ),
        "last_edited_time": (
            page["last_edited_time"].isoformat()
            if isinstance(page["last_edited_time"], datetime)
            else page["last_edited_time"]
        ),
        "title": page["title"],
        "properties": page["properties"],
        "parent": (
            {"type": "page_id", "page_id": page["parent_id"]}
            if page.get("parent_id")
            else {"type": "workspace", "workspace": True}
        ),
    }


@app.patch("/pages/{page_id}", response_model=Dict[str, Any])
async def update_page(page_id: str, update_data: Dict[str, Any] = Body(...)):
    """
    ページを更新（モック）
    """
    logger.info(f"Updating page with ID: {page_id}")

    if page_id not in pages_db:
        raise HTTPException(status_code=404, detail="Page not found")

    page = pages_db[page_id]

    # 更新可能なフィールド
    if "title" in update_data:
        page["title"] = update_data["title"]

    if "properties" in update_data:
        for key, value in update_data["properties"].items():
            page["properties"][key] = value

    if "content" in update_data:
        page["content"] = update_data["content"]

    # 最終更新時間の更新
    page["last_edited_time"] = datetime.now()

    # 更新したページを保存
    pages_db[page_id] = page

    return {
        "id": page["id"],
        "object": "page",
        "created_time": (
            page["created_time"].isoformat()
            if isinstance(page["created_time"], datetime)
            else page["created_time"]
        ),
        "last_edited_time": (
            page["last_edited_time"].isoformat()
            if isinstance(page["last_edited_time"], datetime)
            else page["last_edited_time"]
        ),
        "title": page["title"],
        "properties": page["properties"],
    }


@app.delete("/pages/{page_id}", response_model=Dict[str, str])
async def delete_page(page_id: str):
    """
    ページを削除（モック）
    """
    logger.info(f"Deleting page with ID: {page_id}")

    if page_id not in pages_db:
        raise HTTPException(status_code=404, detail="Page not found")

    del pages_db[page_id]

    return {"status": "deleted", "page_id": page_id}


@app.post("/databases", response_model=Dict[str, Any])
async def create_database(database: Database):
    """
    データベースを作成（モック）
    """
    logger.info(f"Creating database with title: {database.title}")

    # データベースIDの生成
    database_id = str(uuid.uuid4())
    database.id = database_id
    database.created_time = datetime.now()
    database.last_edited_time = datetime.now()

    # データベースの保存
    databases_db[database_id] = database.dict()

    return {
        "id": database_id,
        "object": "database",
        "created_time": database.created_time.isoformat(),
        "last_edited_time": database.last_edited_time.isoformat(),
        "title": database.title,
        "properties": database.properties,
    }


@app.get("/databases/{database_id}", response_model=Dict[str, Any])
async def get_database(database_id: str):
    """
    データベースを取得（モック）
    """
    logger.info(f"Getting database with ID: {database_id}")

    if database_id not in databases_db:
        raise HTTPException(status_code=404, detail="Database not found")

    database = databases_db[database_id]

    return {
        "id": database["id"],
        "object": "database",
        "created_time": (
            database["created_time"].isoformat()
            if isinstance(database["created_time"], datetime)
            else database["created_time"]
        ),
        "last_edited_time": (
            database["last_edited_time"].isoformat()
            if isinstance(database["last_edited_time"], datetime)
            else database["last_edited_time"]
        ),
        "title": database["title"],
        "properties": database["properties"],
    }


@app.post("/databases/{database_id}/query", response_model=Dict[str, Any])
async def query_database(database_id: str, query: Dict[str, Any] = Body(...)):
    """
    データベースをクエリ（モック）
    """
    logger.info(f"Querying database with ID: {database_id}")

    if database_id not in databases_db:
        raise HTTPException(status_code=404, detail="Database not found")

    # 実際の実装では、ここでクエリに基づいてフィルタリングを行う
    # このモックでは、単純にすべてのページを返す

    results = []
    for page_id, page in pages_db.items():
        if page.get("parent_id") == database_id:
            results.append(
                {
                    "id": page["id"],
                    "object": "page",
                    "created_time": (
                        page["created_time"].isoformat()
                        if isinstance(page["created_time"], datetime)
                        else page["created_time"]
                    ),
                    "last_edited_time": (
                        page["last_edited_time"].isoformat()
                        if isinstance(page["last_edited_time"], datetime)
                        else page["last_edited_time"]
                    ),
                    "title": page["title"],
                    "properties": page["properties"],
                }
            )

    return {
        "object": "list",
        "results": results,
        "has_more": False,
        "next_cursor": None,
    }


@app.get("/mcp/operations", response_model=Dict[str, List[str]])
async def get_operations():
    """
    サポートされているMCP操作を取得
    """
    return {
        "operations": [
            "create_page",
            "get_page",
            "update_page",
            "delete_page",
            "create_database",
            "get_database",
            "query_database",
        ]
    }


@app.post("/mcp/execute", response_model=Dict[str, Any])
async def execute_operation(operation: Dict[str, Any] = Body(...)):
    """
    MCP操作を実行
    """
    operation_name = operation.get("operation")
    params = operation.get("params", {})

    logger.info(f"Executing MCP operation: {operation_name}")

    if operation_name == "create_page":
        page = Page(**params)
        result = await create_page(page)
        return {"status": "success", "data": result}

    elif operation_name == "get_page":
        page_id = params.get("page_id")
        if not page_id:
            raise HTTPException(status_code=400, detail="page_id is required")
        result = await get_page(page_id)
        return {"status": "success", "data": result}

    elif operation_name == "update_page":
        page_id = params.get("page_id")
        update_data = params.get("update_data", {})
        if not page_id:
            raise HTTPException(status_code=400, detail="page_id is required")
        result = await update_page(page_id, update_data)
        return {"status": "success", "data": result}

    elif operation_name == "delete_page":
        page_id = params.get("page_id")
        if not page_id:
            raise HTTPException(status_code=400, detail="page_id is required")
        result = await delete_page(page_id)
        return {"status": "success", "data": result}

    elif operation_name == "create_database":
        database = Database(**params)
        result = await create_database(database)
        return {"status": "success", "data": result}

    elif operation_name == "get_database":
        database_id = params.get("database_id")
        if not database_id:
            raise HTTPException(status_code=400, detail="database_id is required")
        result = await get_database(database_id)
        return {"status": "success", "data": result}

    elif operation_name == "query_database":
        database_id = params.get("database_id")
        query = params.get("query", {})
        if not database_id:
            raise HTTPException(status_code=400, detail="database_id is required")
        result = await query_database(database_id, query)
        return {"status": "success", "data": result}

    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown operation: {operation_name}"
        )
