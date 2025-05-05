import base64
import json
import logging
import os
from typing import Dict, Optional, Any

from src.security.encryption.data_encryption import DataEncryption

logger = logging.getLogger(__name__)


class KeyManager:
    """
    暗号化キーを管理するクラス
    """

    def __init__(self, config, secrets_manager=None):
        """
        初期化

        Args:
            config: アプリケーション設定
            secrets_manager: SecretsManagerインスタンス（オプション）
        """
        self.config = config
        self.secrets_manager = secrets_manager
        self.keys = {}
        self.master_key = None
        self._initialize_master_key()

    def _initialize_master_key(self) -> None:
        """
        マスターキーの初期化
        """
        # AWS Secrets Managerが有効な場合
        if self.config.AWS_SECRET_MANAGER_ENABLED and self.secrets_manager:
            self._load_master_key_from_secrets_manager()
        else:
            self._load_master_key_from_file()

    def _load_master_key_from_secrets_manager(self) -> None:
        """
        AWS Secrets Managerからマスターキーを読み込み
        """
        try:
            secret_name = f"{self.config.APP_NAME}/master_key"
            logger.info("Loading master key from Secrets Manager")

            secret_data = self.secrets_manager.get_secret(secret_name)
            if secret_data and "key" in secret_data:
                self.master_key = base64.urlsafe_b64decode(secret_data["key"])
                logger.info("Master key loaded from Secrets Manager")
            else:
                # マスターキーが存在しない場合は新規作成
                self._create_new_master_key()

                # Secrets Managerに保存
                self.secrets_manager.create_secret(
                    secret_name,
                    {"key": base64.urlsafe_b64encode(self.master_key).decode()},
                )
                logger.info("New master key created and saved to Secrets Manager")
        except Exception as e:
            logger.error(f"Error loading master key from Secrets Manager: {e}")
            self._create_new_master_key()

    def _load_master_key_from_file(self) -> None:
        """
        ファイルからマスターキーを読み込み
        """
        key_file = os.path.join(
            os.path.dirname(self.config.LOG_FILE), "master_key.json"
        )

        try:
            if os.path.exists(key_file):
                with open(key_file, "r") as f:
                    data = json.load(f)
                    self.master_key = base64.urlsafe_b64decode(data["key"])
                    logger.info("Master key loaded from file")
            else:
                # マスターキーが存在しない場合は新規作成
                self._create_new_master_key()

                # ファイルに保存
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                with open(key_file, "w") as f:
                    json.dump(
                        {"key": base64.urlsafe_b64encode(self.master_key).decode()}, f
                    )
                logger.info("New master key created and saved to file")
        except Exception as e:
            logger.error(f"Error loading master key from file: {e}")
            self._create_new_master_key()

    def _create_new_master_key(self) -> None:
        """
        新しいマスターキーを生成
        """
        self.master_key = DataEncryption().get_key()
        logger.info("New master key created")

    def get_encryption_for_service(self, service_type: str) -> DataEncryption:
        """
        サービス用の暗号化インスタンスを取得

        Args:
            service_type: サービスタイプ

        Returns:
            DataEncryption: 暗号化インスタンス
        """
        if service_type not in self.keys:
            # サービス用のキーを生成
            service_key = DataEncryption().get_key()
            self.keys[service_type] = service_key
            logger.info(f"New encryption key created for service: {service_type}")

        return DataEncryption(key=self.keys[service_type])

    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        機密データを暗号化

        Args:
            data: 暗号化するデータ

        Returns:
            Dict[str, Any]: 暗号化されたデータ
        """
        if not self.master_key:
            logger.error("Master key not initialized")
            return data

        encryption = DataEncryption(key=self.master_key)
        result = {}

        for key, value in data.items():
            if (
                key.endswith("_password")
                or key.endswith("_secret")
                or key.endswith("_key")
                or key == "password"
                or key == "secret"
                or key == "key"
            ):
                # 機密データを暗号化
                if isinstance(value, str):
                    result[key] = encryption.encrypt_to_string(value)
                    result[f"{key}_encrypted"] = True
                else:
                    result[key] = value
            else:
                result[key] = value

        return result

    def decrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        暗号化された機密データを復号化

        Args:
            data: 復号化するデータ

        Returns:
            Dict[str, Any]: 復号化されたデータ
        """
        if not self.master_key:
            logger.error("Master key not initialized")
            return data

        encryption = DataEncryption(key=self.master_key)
        result = {}

        for key, value in data.items():
            if key.endswith("_encrypted"):
                # 暗号化フラグは無視
                continue

            if (
                f"{key}_encrypted" in data
                and data[f"{key}_encrypted"]
                and isinstance(value, str)
            ):
                # 暗号化されたデータを復号化
                try:
                    result[key] = encryption.decrypt_from_string(value).decode()
                except Exception as e:
                    logger.error(f"Error decrypting {key}: {e}")
                    result[key] = value
            else:
                result[key] = value

        return result

    def rotate_master_key(self) -> bool:
        """
        マスターキーのローテーション

        Returns:
            bool: 成功した場合はTrue、失敗した場合はFalse
        """
        try:
            # 古いマスターキーを保存
            old_master_key = self.master_key

            # 新しいマスターキーを生成
            self._create_new_master_key()

            # サービスキーを再暗号化
            for service_type, key in self.keys.items():
                # 古いマスターキーで復号化
                old_encryption = DataEncryption(key=old_master_key)

                # 新しいマスターキーで暗号化
                new_encryption = DataEncryption(key=self.master_key)

                # キーの更新
                self.keys[service_type] = key

            # マスターキーを保存
            if self.config.AWS_SECRET_MANAGER_ENABLED and self.secrets_manager:
                secret_name = f"{self.config.APP_NAME}/master_key"
                self.secrets_manager.update_secret(
                    secret_name,
                    {"key": base64.urlsafe_b64encode(self.master_key).decode()},
                )
            else:
                key_file = os.path.join(
                    os.path.dirname(self.config.LOG_FILE), "master_key.json"
                )
                with open(key_file, "w") as f:
                    json.dump(
                        {"key": base64.urlsafe_b64encode(self.master_key).decode()}, f
                    )

            logger.info("Master key rotated successfully")
            return True
        except Exception as e:
            logger.error(f"Error rotating master key: {e}")
            return False
