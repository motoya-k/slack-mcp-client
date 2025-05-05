import pytest
from unittest.mock import MagicMock
import os
import sys

# テスト用のパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import Config


@pytest.fixture
def test_config():
    """テスト用の設定オブジェクトを提供します"""
    config = Config()
    config.DEBUG = True
    return config


@pytest.fixture
def mock_slack_client():
    """Slackクライアントのモックを提供します"""
    client = MagicMock()
    client.post_message.return_value = {"ok": True}
    client.update_message.return_value = {"ok": True}
    client.get_user_info.return_value = {
        "ok": True,
        "user": {"id": "U12345678", "name": "testuser", "real_name": "Test User"},
    }
    return client


@pytest.fixture
def mock_fast_agent():
    """fast-agentのモックを提供します"""
    agent = MagicMock()
    agent.process_event.return_value = {"status": "success"}
    agent.execute_task.return_value = {"task_id": "task123", "status": "completed"}
    return agent


@pytest.fixture
def mock_mcp_client():
    """MCPクライアントのモックを提供します"""
    client = MagicMock()
    client.connect.return_value = True
    client.execute_operation.return_value = {"status": "success", "data": {}}
    client.get_resource.return_value = {"id": "resource123", "data": {}}
    return client


@pytest.fixture
def mock_postgresql_connector():
    """PostgreSQLコネクタのモックを提供します"""
    connector = MagicMock()
    connector.connect.return_value = True
    connector.is_connected.return_value = True
    connector.execute_query.return_value = {
        "columns": ["id", "name"],
        "rows": [(1, "test1"), (2, "test2")],
    }
    return connector


@pytest.fixture
def mock_gmail_connector():
    """Gmailコネクタのモックを提供します"""
    connector = MagicMock()
    connector.connect.return_value = True
    connector.is_connected.return_value = True
    connector.send_email.return_value = {"message_id": "msg123"}
    connector.get_emails.return_value = [
        {"id": "email1", "subject": "Test Email", "body": "Test Body"}
    ]
    return connector


@pytest.fixture
def mock_notion_connector():
    """Notionコネクタのモックを提供します"""
    connector = MagicMock()
    connector.connect.return_value = True
    connector.is_connected.return_value = True
    connector.get_page.return_value = {"id": "page123", "title": "Test Page"}
    connector.update_page.return_value = {"id": "page123", "updated": True}
    connector.create_page.return_value = {"id": "newpage123", "created": True}
    return connector
