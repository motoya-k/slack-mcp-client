import logging
from typing import Dict, List, Set, Optional, Any

from src.security.authorization.permission import Permission, PermissionSet
from src.security.authorization.role import Role, RoleRegistry

logger = logging.getLogger(__name__)


class AccessControl:
    """
    アクセス制御を管理するクラス
    """

    def __init__(self):
        """
        初期化
        """
        self.role_registry = RoleRegistry()
        self.user_roles = {}  # user_id -> [role_names]
        self.channel_roles = {}  # channel_id -> [role_names]

    def add_role(self, role: Role) -> None:
        """
        ロールを追加

        Args:
            role: 追加するロール
        """
        self.role_registry.add_role(role)

    def assign_role_to_user(self, user_id: str, role_name: str) -> bool:
        """
        ユーザーにロールを割り当て

        Args:
            user_id: ユーザーID
            role_name: ロール名

        Returns:
            bool: 割り当てが成功した場合はTrue、失敗した場合はFalse
        """
        if role_name not in self.role_registry.get_role_names():
            logger.error(f"Role does not exist: {role_name}")
            return False

        if user_id not in self.user_roles:
            self.user_roles[user_id] = []

        if role_name not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role_name)
            logger.info(f"Assigned role {role_name} to user {user_id}")

        return True

    def remove_role_from_user(self, user_id: str, role_name: str) -> bool:
        """
        ユーザーからロールを削除

        Args:
            user_id: ユーザーID
            role_name: ロール名

        Returns:
            bool: 削除が成功した場合はTrue、失敗した場合はFalse
        """
        if user_id not in self.user_roles:
            return False

        if role_name in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role_name)
            logger.info(f"Removed role {role_name} from user {user_id}")
            return True

        return False

    def assign_role_to_channel(self, channel_id: str, role_name: str) -> bool:
        """
        チャンネルにロールを割り当て

        Args:
            channel_id: チャンネルID
            role_name: ロール名

        Returns:
            bool: 割り当てが成功した場合はTrue、失敗した場合はFalse
        """
        if role_name not in self.role_registry.get_role_names():
            logger.error(f"Role does not exist: {role_name}")
            return False

        if channel_id not in self.channel_roles:
            self.channel_roles[channel_id] = []

        if role_name not in self.channel_roles[channel_id]:
            self.channel_roles[channel_id].append(role_name)
            logger.info(f"Assigned role {role_name} to channel {channel_id}")

        return True

    def remove_role_from_channel(self, channel_id: str, role_name: str) -> bool:
        """
        チャンネルからロールを削除

        Args:
            channel_id: チャンネルID
            role_name: ロール名

        Returns:
            bool: 削除が成功した場合はTrue、失敗した場合はFalse
        """
        if channel_id not in self.channel_roles:
            return False

        if role_name in self.channel_roles[channel_id]:
            self.channel_roles[channel_id].remove(role_name)
            logger.info(f"Removed role {role_name} from channel {channel_id}")
            return True

        return False

    def get_user_roles(self, user_id: str) -> List[str]:
        """
        ユーザーのロールを取得

        Args:
            user_id: ユーザーID

        Returns:
            List[str]: ロール名のリスト
        """
        return self.user_roles.get(user_id, [])

    def get_channel_roles(self, channel_id: str) -> List[str]:
        """
        チャンネルのロールを取得

        Args:
            channel_id: チャンネルID

        Returns:
            List[str]: ロール名のリスト
        """
        return self.channel_roles.get(channel_id, [])

    def get_user_permissions(self, user_id: str) -> PermissionSet:
        """
        ユーザーの権限を取得

        Args:
            user_id: ユーザーID

        Returns:
            PermissionSet: 権限セット
        """
        permissions = PermissionSet()

        # ユーザーのロールから権限を取得
        for role_name in self.get_user_roles(user_id):
            role = self.role_registry.get_role(role_name)
            if role:
                for permission in role.permissions:
                    permissions.add(permission)

        return permissions

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        ユーザーが権限を持っているか確認

        Args:
            user_id: ユーザーID
            permission: 確認する権限

        Returns:
            bool: 権限を持っている場合はTrue、そうでない場合はFalse
        """
        user_permissions = self.get_user_permissions(user_id)
        return user_permissions.has(permission)

    def can_access_channel(self, user_id: str, channel_id: str) -> bool:
        """
        ユーザーがチャンネルにアクセスできるか確認

        Args:
            user_id: ユーザーID
            channel_id: チャンネルID

        Returns:
            bool: アクセスできる場合はTrue、そうでない場合はFalse
        """
        # 管理者は全てのチャンネルにアクセス可能
        if self.has_permission(user_id, Permission.ADMIN):
            return True

        # ユーザーのロールとチャンネルのロールを比較
        user_roles = set(self.get_user_roles(user_id))
        channel_roles = set(self.get_channel_roles(channel_id))

        # ロールが一致するか確認
        return len(user_roles.intersection(channel_roles)) > 0

    def can_execute_operation(self, user_id: str, service: str, operation: str) -> bool:
        """
        ユーザーが操作を実行できるか確認

        Args:
            user_id: ユーザーID
            service: サービス名
            operation: 操作名

        Returns:
            bool: 実行できる場合はTrue、そうでない場合はFalse
        """
        # 管理者は全ての操作を実行可能
        if self.has_permission(user_id, Permission.ADMIN):
            return True

        # サービスと操作に基づいて必要な権限を判断
        required_permission = None

        if service == "postgresql":
            if operation.startswith("query"):
                required_permission = Permission.QUERY_DATABASE
            elif (
                operation.startswith("modify")
                or operation.startswith("update")
                or operation.startswith("insert")
                or operation.startswith("delete")
            ):
                required_permission = Permission.MODIFY_DATABASE

        elif service == "gmail":
            if operation.startswith("send"):
                required_permission = Permission.SEND_EMAIL
            elif operation.startswith("get") or operation.startswith("read"):
                required_permission = Permission.READ_EMAIL

        elif service == "notion":
            if operation.startswith("get") or operation.startswith("read"):
                required_permission = Permission.READ_NOTION
            elif operation.startswith("create") or operation.startswith("update"):
                required_permission = Permission.WRITE_NOTION

        # 必要な権限が判断できない場合はアクセス拒否
        if required_permission is None:
            logger.warning(f"Unknown operation: {service}.{operation}")
            return False

        # 権限を確認
        return self.has_permission(user_id, required_permission)
