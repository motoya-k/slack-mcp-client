-- データベースの作成
-- CREATE DATABASE mcp_client;

-- ユーザーテーブルの作成
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ロールテーブルの作成
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ユーザーロールテーブルの作成
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- チャンネルテーブルの作成
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- チャンネルロールテーブルの作成
CREATE TABLE IF NOT EXISTS channel_roles (
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (channel_id, role_id)
);

-- 監査ログテーブルの作成
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    resource VARCHAR(255),
    action VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    details JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    session_id VARCHAR(100),
    request_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- デフォルトロールの挿入
INSERT INTO roles (name, description) VALUES
    ('admin', 'システム管理者'),
    ('user', '一般ユーザー'),
    ('readonly', '読み取り専用ユーザー'),
    ('db_admin', 'データベース管理者'),
    ('mail_admin', 'メール管理者'),
    ('notion_admin', 'Notion管理者')
ON CONFLICT (name) DO NOTHING;

-- デフォルト管理者ユーザーの挿入
INSERT INTO users (user_id, username, email, is_admin) VALUES
    ('U12345678', 'admin', 'admin@example.com', TRUE)
ON CONFLICT (user_id) DO NOTHING;

-- 管理者ユーザーにadminロールを割り当て
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u, roles r
WHERE u.user_id = 'U12345678' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

-- インデックスの作成
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_status ON audit_logs(status);
