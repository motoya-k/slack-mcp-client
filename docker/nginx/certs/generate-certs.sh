#!/bin/bash

# 自己署名SSL証明書を生成するスクリプト
# 開発環境でのみ使用してください

# 証明書の設定
COUNTRY="JP"
STATE="Tokyo"
LOCALITY="Tokyo"
ORGANIZATION="Slack MCP Client"
ORGANIZATIONAL_UNIT="Development"
COMMON_NAME="localhost"
EMAIL="admin@example.com"

# 証明書の生成先ディレクトリ
CERT_DIR="$(dirname "$0")"

# 秘密鍵の生成
openssl genrsa -out "${CERT_DIR}/server.key" 2048

# 証明書署名要求（CSR）の生成
openssl req -new -key "${CERT_DIR}/server.key" -out "${CERT_DIR}/server.csr" -subj "/C=${COUNTRY}/ST=${STATE}/L=${LOCALITY}/O=${ORGANIZATION}/OU=${ORGANIZATIONAL_UNIT}/CN=${COMMON_NAME}/emailAddress=${EMAIL}"

# 自己署名証明書の生成
openssl x509 -req -days 365 -in "${CERT_DIR}/server.csr" -signkey "${CERT_DIR}/server.key" -out "${CERT_DIR}/server.crt"

# CSRファイルの削除（不要）
rm "${CERT_DIR}/server.csr"

echo "自己署名SSL証明書が生成されました:"
echo "- 秘密鍵: ${CERT_DIR}/server.key"
echo "- 証明書: ${CERT_DIR}/server.crt"
echo ""
echo "注意: これは開発環境用の自己署名証明書です。本番環境では信頼された認証局による証明書を使用してください。"
