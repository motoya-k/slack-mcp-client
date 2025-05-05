import logging
import json
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ServiceAuthenticator:
    """
    外部サービスの認証情報を管理するクラス
    """

    def __init__(self, config):
        """
        初期化

        Args:
            config: アプリケーション設定
        """
        self.config = config
        self.credentials = {}
        self.secrets_manager = None

    def set_secrets_manager(self, secrets_manager):
        """
        SecretsManagerを設定

        Args:
            secrets_manager: SecretsManagerインスタンス
        """
        self.secrets_manager = secrets_manager

    def load_credentials(self, service_type: str) -> bool:
        """
        サービスの認証情報を読み込み

        Args:
            service_type: サービスタイプ

        Returns:
            bool: 読み込みが成功した場合はTrue、失敗した場合はFalse
        """
        # AWS Secrets Managerが有効な場合
        if self.config.AWS_SECRET_MANAGER_ENABLED and self.secrets_manager:
            return self._load_from_secrets_manager(service_type)

        # 環境変数または設定から読み込み
        return self._load_from_config(service_type)

    def _load_from_secrets_manager(self, service_type: str) -> bool:
        """
        AWS Secrets Managerからサービスの認証情報を読み込み

        Args:
            service_type: サービスタイプ

        Returns:
            bool: 読み込みが成功した場合はTrue、失敗した場合はFalse
        """
        if not self.secrets_manager:
            logger.error("Secrets manager not set")
            return False

        try:
            secret_name = f"{self.config.APP_NAME}/{service_type}"
            logger.info(f"Loading credentials for {service_type} from Secrets Manager")

            secret_data = self.secrets_manager.get_secret(secret_name)
            if not secret_data:
                logger.error(
                    f"No credentials found for {service_type} in Secrets Manager"
                )
                return False

            self.credentials[service_type] = secret_data
            logger.info(f"Credentials for {service_type} loaded from Secrets Manager")
            return True
        except Exception as e:
            logger.error(
                f"Error loading credentials for {service_type} from Secrets Manager: {e}"
            )
            return False

    def _load_from_config(self, service_type: str) -> bool:
        """
        設定からサービスの認証情報を読み込み

        Args:
            service_type: サービスタイプ

        Returns:
            bool: 読み込みが成功した場合はTrue、失敗した場合はFalse
        """
        try:
            if service_type == "postgresql":
                self.credentials[service_type] = {
                    "host": self.config.PG_HOST,
                    "port": self.config.PG_PORT,
                    "database": self.config.PG_DATABASE,
                    "user": self.config.PG_USER,
                    "password": self.config.PG_PASSWORD,
                }
                logger.info(f"Credentials for {service_type} loaded from config")
                return True

            elif service_type == "gmail":
                credentials_file = self.config.GMAIL_CREDENTIALS_FILE
                if not credentials_file or not os.path.exists(credentials_file):
                    logger.error(
                        f"Gmail credentials file not found: {credentials_file}"
                    )
                    return False

                try:
                    with open(credentials_file, "r") as f:
                        self.credentials[service_type] = json.load(f)
                    logger.info(f"Credentials for {service_type} loaded from file")
                    return True
                except Exception as e:
                    logger.error(f"Error loading Gmail credentials from file: {e}")
                    return False

            elif service_type == "notion":
                self.credentials[service_type] = {"token": self.config.NOTION_TOKEN}
                logger.info(f"Credentials for {service_type} loaded from config")
                return True

            else:
                logger.error(f"Unknown service type: {service_type}")
                return False

        except Exception as e:
            logger.error(
                f"Error loading credentials for {service_type} from config: {e}"
            )
            return False

    def get_credentials(self, service_type: str) -> Optional[Dict[str, Any]]:
        """
        サービスの認証情報を取得

        Args:
            service_type: サービスタイプ

        Returns:
            Optional[Dict[str, Any]]: 認証情報、取得できない場合はNone
        """
        # 認証情報がまだ読み込まれていない場合は読み込み
        if service_type not in self.credentials:
            if not self.load_credentials(service_type):
                return None

        return self.credentials.get(service_type)

    def update_credentials(
        self, service_type: str, credentials: Dict[str, Any]
    ) -> bool:
        """
        サービスの認証情報を更新

        Args:
            service_type: サービスタイプ
            credentials: 新しい認証情報

        Returns:
            bool: 更新が成功した場合はTrue、失敗した場合はFalse
        """
        # AWS Secrets Managerが有効な場合
        if self.config.AWS_SECRET_MANAGER_ENABLED and self.secrets_manager:
            try:
                secret_name = f"{self.config.APP_NAME}/{service_type}"
                logger.info(
                    f"Updating credentials for {service_type} in Secrets Manager"
                )

                self.secrets_manager.update_secret(secret_name, credentials)
                self.credentials[service_type] = credentials
                logger.info(
                    f"Credentials for {service_type} updated in Secrets Manager"
                )
                return True
            except Exception as e:
                logger.error(
                    f"Error updating credentials for {service_type} in Secrets Manager: {e}"
                )
                return False

        # 環境変数または設定の場合は、メモリ内のみ更新
        self.credentials[service_type] = credentials
        logger.info(f"Credentials for {service_type} updated in memory")
        return True
