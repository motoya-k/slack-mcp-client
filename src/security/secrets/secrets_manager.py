import boto3
import json
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    AWS Secrets Managerとの連携を管理するクラス
    """

    def __init__(self, config):
        """
        初期化

        Args:
            config: アプリケーション設定
        """
        self.config = config
        self.client = boto3.client("secretsmanager", region_name=config.AWS_REGION)

    def get_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """
        シークレットを取得

        Args:
            secret_name: シークレット名

        Returns:
            Optional[Dict[str, Any]]: シークレット値、取得できない場合はNone
        """
        try:
            logger.info(f"Getting secret: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)

            if "SecretString" in response:
                secret = json.loads(response["SecretString"])
                logger.info(f"Secret {secret_name} retrieved successfully")
                return secret
            else:
                # バイナリシークレットの場合
                logger.info(f"Binary secret {secret_name} retrieved successfully")
                return {"binary": response["SecretBinary"]}

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.error(f"Secret {secret_name} not found")
            elif e.response["Error"]["Code"] == "InvalidParameterException":
                logger.error(f"Invalid parameter for secret {secret_name}")
            elif e.response["Error"]["Code"] == "InvalidRequestException":
                logger.error(f"Invalid request for secret {secret_name}")
            elif e.response["Error"]["Code"] == "DecryptionFailure":
                logger.error(f"Decryption failure for secret {secret_name}")
            elif e.response["Error"]["Code"] == "InternalServiceError":
                logger.error(f"Internal service error for secret {secret_name}")
            else:
                logger.error(f"Unknown error getting secret {secret_name}: {e}")

            return None

        except Exception as e:
            logger.error(f"Error getting secret {secret_name}: {e}")
            return None

    def create_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """
        シークレットを作成

        Args:
            secret_name: シークレット名
            secret_value: シークレット値

        Returns:
            bool: 作成が成功した場合はTrue、失敗した場合はFalse
        """
        try:
            logger.info(f"Creating secret: {secret_name}")
            self.client.create_secret(
                Name=secret_name, SecretString=json.dumps(secret_value)
            )
            logger.info(f"Secret {secret_name} created successfully")
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceExistsException":
                logger.warning(f"Secret {secret_name} already exists")
                # 既に存在する場合は更新
                return self.update_secret(secret_name, secret_value)
            else:
                logger.error(f"Error creating secret {secret_name}: {e}")
                return False

        except Exception as e:
            logger.error(f"Error creating secret {secret_name}: {e}")
            return False

    def update_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """
        シークレットを更新

        Args:
            secret_name: シークレット名
            secret_value: 新しいシークレット値

        Returns:
            bool: 更新が成功した場合はTrue、失敗した場合はFalse
        """
        try:
            logger.info(f"Updating secret: {secret_name}")
            self.client.update_secret(
                SecretId=secret_name, SecretString=json.dumps(secret_value)
            )
            logger.info(f"Secret {secret_name} updated successfully")
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.warning(f"Secret {secret_name} not found, creating new secret")
                # 存在しない場合は作成
                return self.create_secret(secret_name, secret_value)
            else:
                logger.error(f"Error updating secret {secret_name}: {e}")
                return False

        except Exception as e:
            logger.error(f"Error updating secret {secret_name}: {e}")
            return False

    def delete_secret(self, secret_name: str, force_delete: bool = False) -> bool:
        """
        シークレットを削除

        Args:
            secret_name: シークレット名
            force_delete: 強制削除フラグ（Trueの場合、復旧期間なしで削除）

        Returns:
            bool: 削除が成功した場合はTrue、失敗した場合はFalse
        """
        try:
            logger.info(f"Deleting secret: {secret_name}")

            if force_delete:
                self.client.delete_secret(
                    SecretId=secret_name, ForceDeleteWithoutRecovery=True
                )
            else:
                self.client.delete_secret(SecretId=secret_name, RecoveryWindowInDays=7)

            logger.info(f"Secret {secret_name} deleted successfully")
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.warning(f"Secret {secret_name} not found")
                return True  # 既に存在しない場合は成功とみなす
            else:
                logger.error(f"Error deleting secret {secret_name}: {e}")
                return False

        except Exception as e:
            logger.error(f"Error deleting secret {secret_name}: {e}")
            return False
