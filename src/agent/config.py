from typing import Dict, Any, Optional


class FastAgentConfig:
    """
    fast-agent用の設定クラス
    """

    def __init__(self, config):
        """
        初期化

        Args:
            config: アプリケーション設定
        """
        self.api_key = config.FAST_AGENT_API_KEY
        self.timeout = config.FAST_AGENT_TIMEOUT
        self.debug = config.DEBUG

    def to_dict(self) -> Dict[str, Any]:
        """
        設定を辞書形式で取得

        Returns:
            Dict[str, Any]: 設定の辞書
        """
        return {"api_key": self.api_key, "timeout": self.timeout, "debug": self.debug}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FastAgentConfig":
        """
        辞書から設定を作成

        Args:
            data: 設定データの辞書

        Returns:
            FastAgentConfig: 設定オブジェクト
        """
        config = type("Config", (), {})()
        config.FAST_AGENT_API_KEY = data.get("api_key")
        config.FAST_AGENT_TIMEOUT = data.get("timeout", 30)
        config.DEBUG = data.get("debug", False)

        return cls(config)
