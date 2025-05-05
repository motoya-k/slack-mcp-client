from enum import Enum, auto
from typing import Set, List, Dict, Any


class Permission(Enum):
    """
    システム内の権限を定義する列挙型
    """

    # 一般的な権限
    VIEW_PUBLIC = auto()  # 公開情報の閲覧

    # Slack関連の権限
    SEND_MESSAGE = auto()  # メッセージ送信
    MANAGE_CHANNELS = auto()  # チャンネル管理

    # PostgreSQL関連の権限
    QUERY_DATABASE = auto()  # データベースクエリ実行
    MODIFY_DATABASE = auto()  # データベース変更

    # Gmail関連の権限
    SEND_EMAIL = auto()  # メール送信
    READ_EMAIL = auto()  # メール読み取り

    # Notion関連の権限
    READ_NOTION = auto()  # Notionページ読み取り
    WRITE_NOTION = auto()  # Notionページ書き込み

    # 管理者権限
    ADMIN = auto()  # 管理者権限
    MANAGE_USERS = auto()  # ユーザー管理
    MANAGE_PERMISSIONS = auto()  # 権限管理
    MANAGE_CONNECTORS = auto()  # コネクタ管理
    VIEW_LOGS = auto()  # ログ閲覧
    MANAGE_SYSTEM = auto()  # システム管理


class PermissionSet:
    """
    権限セットを管理するクラス
    """

    def __init__(self, permissions: Set[Permission] = None):
        """
        初期化

        Args:
            permissions: 初期権限セット
        """
        self.permissions = permissions or set()

    def add(self, permission: Permission) -> None:
        """
        権限を追加

        Args:
            permission: 追加する権限
        """
        self.permissions.add(permission)

    def remove(self, permission: Permission) -> None:
        """
        権限を削除

        Args:
            permission: 削除する権限
        """
        if permission in self.permissions:
            self.permissions.remove(permission)

    def has(self, permission: Permission) -> bool:
        """
        権限を持っているか確認

        Args:
            permission: 確認する権限

        Returns:
            bool: 権限を持っている場合はTrue、そうでない場合はFalse
        """
        # ADMIN権限は全ての権限を含む
        if Permission.ADMIN in self.permissions:
            return True

        return permission in self.permissions

    def has_any(self, permissions: List[Permission]) -> bool:
        """
        いずれかの権限を持っているか確認

        Args:
            permissions: 確認する権限のリスト

        Returns:
            bool: いずれかの権限を持っている場合はTrue、そうでない場合はFalse
        """
        # ADMIN権限は全ての権限を含む
        if Permission.ADMIN in self.permissions:
            return True

        return any(permission in self.permissions for permission in permissions)

    def has_all(self, permissions: List[Permission]) -> bool:
        """
        全ての権限を持っているか確認

        Args:
            permissions: 確認する権限のリスト

        Returns:
            bool: 全ての権限を持っている場合はTrue、そうでない場合はFalse
        """
        # ADMIN権限は全ての権限を含む
        if Permission.ADMIN in self.permissions:
            return True

        return all(permission in self.permissions for permission in permissions)

    def to_list(self) -> List[str]:
        """
        権限リストを文字列のリストとして取得

        Returns:
            List[str]: 権限名のリスト
        """
        return [permission.name for permission in self.permissions]

    @classmethod
    def from_list(cls, permission_names: List[str]) -> "PermissionSet":
        """
        文字列のリストから権限セットを作成

        Args:
            permission_names: 権限名のリスト

        Returns:
            PermissionSet: 権限セット
        """
        permissions = set()
        for name in permission_names:
            try:
                permission = Permission[name]
                permissions.add(permission)
            except KeyError:
                # 無効な権限名は無視
                pass

        return cls(permissions)

    def __contains__(self, permission: Permission) -> bool:
        """
        権限を持っているか確認（in演算子のサポート）

        Args:
            permission: 確認する権限

        Returns:
            bool: 権限を持っている場合はTrue、そうでない場合はFalse
        """
        return self.has(permission)

    def __iter__(self):
        """
        イテレータの実装

        Returns:
            Iterator: 権限のイテレータ
        """
        return iter(self.permissions)

    def __len__(self) -> int:
        """
        権限の数を取得

        Returns:
            int: 権限の数
        """
        return len(self.permissions)
