import logging
from typing import Dict, Set, List, Optional

from src.security.authorization.permission import Permission, PermissionSet

logger = logging.getLogger(__name__)


class Role:
    """
    ユーザーロールを表すクラス
    """

    def __init__(
        self, name: str, description: str = "", permissions: PermissionSet = None
    ):
        """
        初期化

        Args:
            name: ロール名
            description: ロールの説明
            permissions: 権限セット
        """
        self.name = name
        self.description = description
        self.permissions = permissions or PermissionSet()

    def add_permission(self, permission: Permission) -> None:
        """
        権限を追加

        Args:
            permission: 追加する権限
        """
        self.permissions.add(permission)
        logger.debug(f"Added permission {permission.name} to role {self.name}")

    def remove_permission(self, permission: Permission) -> None:
        """
        権限を削除

        Args:
            permission: 削除する権限
        """
        self.permissions.remove(permission)
        logger.debug(f"Removed permission {permission.name} from role {self.name}")

    def has_permission(self, permission: Permission) -> bool:
        """
        権限を持っているか確認

        Args:
            permission: 確認する権限

        Returns:
            bool: 権限を持っている場合はTrue、そうでない場合はFalse
        """
        return self.permissions.has(permission)

    def to_dict(self) -> Dict:
        """
        ロール情報を辞書として取得

        Returns:
            Dict: ロール情報の辞書
        """
        return {
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions.to_list(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Role":
        """
        辞書からロールを作成

        Args:
            data: ロール情報の辞書

        Returns:
            Role: ロールオブジェクト
        """
        name = data.get("name", "")
        description = data.get("description", "")
        permission_names = data.get("permissions", [])
        permissions = PermissionSet.from_list(permission_names)

        return cls(name, description, permissions)


class RoleRegistry:
    """
    ロールを管理するレジストリ
    """

    def __init__(self):
        """
        初期化
        """
        self.roles = {}
        self._initialize_default_roles()

    def _initialize_default_roles(self) -> None:
        """
        デフォルトロールの初期化
        """
        # 管理者ロール
        admin_role = Role("admin", "システム管理者")
        admin_role.add_permission(Permission.ADMIN)
        self.add_role(admin_role)

        # 一般ユーザーロール
        user_role = Role("user", "一般ユーザー")
        user_role.add_permission(Permission.VIEW_PUBLIC)
        user_role.add_permission(Permission.SEND_MESSAGE)
        self.add_role(user_role)

        # 読み取り専用ロール
        readonly_role = Role("readonly", "読み取り専用ユーザー")
        readonly_role.add_permission(Permission.VIEW_PUBLIC)
        self.add_role(readonly_role)

        # データベース管理者ロール
        db_admin_role = Role("db_admin", "データベース管理者")
        db_admin_role.add_permission(Permission.QUERY_DATABASE)
        db_admin_role.add_permission(Permission.MODIFY_DATABASE)
        self.add_role(db_admin_role)

        # メール管理者ロール
        mail_admin_role = Role("mail_admin", "メール管理者")
        mail_admin_role.add_permission(Permission.SEND_EMAIL)
        mail_admin_role.add_permission(Permission.READ_EMAIL)
        self.add_role(mail_admin_role)

        # Notion管理者ロール
        notion_admin_role = Role("notion_admin", "Notion管理者")
        notion_admin_role.add_permission(Permission.READ_NOTION)
        notion_admin_role.add_permission(Permission.WRITE_NOTION)
        self.add_role(notion_admin_role)

    def add_role(self, role: Role) -> None:
        """
        ロールを追加

        Args:
            role: 追加するロール
        """
        self.roles[role.name] = role
        logger.info(f"Added role: {role.name}")

    def get_role(self, role_name: str) -> Optional[Role]:
        """
        ロールを取得

        Args:
            role_name: ロール名

        Returns:
            Optional[Role]: ロールオブジェクト、存在しない場合はNone
        """
        return self.roles.get(role_name)

    def remove_role(self, role_name: str) -> bool:
        """
        ロールを削除

        Args:
            role_name: ロール名

        Returns:
            bool: 削除が成功した場合はTrue、存在しない場合はFalse
        """
        if role_name in self.roles:
            del self.roles[role_name]
            logger.info(f"Removed role: {role_name}")
            return True
        return False

    def get_all_roles(self) -> Dict[str, Role]:
        """
        全てのロールを取得

        Returns:
            Dict[str, Role]: ロール名とロールオブジェクトの辞書
        """
        return self.roles.copy()

    def get_role_names(self) -> List[str]:
        """
        全てのロール名を取得

        Returns:
            List[str]: ロール名のリスト
        """
        return list(self.roles.keys())
