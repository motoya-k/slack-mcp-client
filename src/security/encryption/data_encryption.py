import base64
import logging
import os
from typing import Union, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class DataEncryption:
    """
    データ暗号化を管理するクラス
    """

    def __init__(
        self,
        key: Optional[bytes] = None,
        password: Optional[str] = None,
        salt: Optional[bytes] = None,
    ):
        """
        初期化

        Args:
            key: 暗号化キー（オプション）
            password: パスワード（オプション）
            salt: ソルト（オプション）

        Note:
            - keyが指定された場合、そのキーを使用
            - passwordとsaltが指定された場合、それらからキーを生成
            - いずれも指定されない場合、新しいキーを生成
        """
        if key:
            self.key = key
        elif password:
            # パスワードからキーを生成
            salt = salt or os.urandom(16)
            self.salt = salt
            self.key = self._derive_key_from_password(password, salt)
        else:
            # 新しいキーを生成
            self.key = Fernet.generate_key()

        self.cipher = Fernet(self.key)
        logger.debug("DataEncryption initialized")

    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """
        パスワードからキーを生成

        Args:
            password: パスワード
            salt: ソルト

        Returns:
            bytes: 生成されたキー
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """
        データを暗号化

        Args:
            data: 暗号化するデータ

        Returns:
            bytes: 暗号化されたデータ
        """
        if isinstance(data, str):
            data = data.encode()

        try:
            encrypted_data = self.cipher.encrypt(data)
            logger.debug("Data encrypted successfully")
            return encrypted_data
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        データを復号化

        Args:
            encrypted_data: 暗号化されたデータ

        Returns:
            bytes: 復号化されたデータ

        Raises:
            Exception: 復号化エラー
        """
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
            logger.debug("Data decrypted successfully")
            return decrypted_data
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise

    def encrypt_to_string(self, data: Union[str, bytes]) -> str:
        """
        データを暗号化して文字列として返す

        Args:
            data: 暗号化するデータ

        Returns:
            str: Base64エンコードされた暗号化データ
        """
        encrypted_data = self.encrypt(data)
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt_from_string(self, encrypted_string: str) -> bytes:
        """
        文字列から復号化

        Args:
            encrypted_string: Base64エンコードされた暗号化データ

        Returns:
            bytes: 復号化されたデータ
        """
        encrypted_data = base64.urlsafe_b64decode(encrypted_string)
        return self.decrypt(encrypted_data)

    def get_key(self) -> bytes:
        """
        暗号化キーを取得

        Returns:
            bytes: 暗号化キー
        """
        return self.key

    def get_key_as_string(self) -> str:
        """
        暗号化キーを文字列として取得

        Returns:
            str: Base64エンコードされた暗号化キー
        """
        return self.key.decode()
