import os
import logging
from logging.handlers import RotatingFileHandler
import sys


def setup_logging(config):
    """
    アプリケーションのロギング設定を行います。

    Args:
        config: アプリケーション設定オブジェクト
    """
    # ログディレクトリの作成
    log_dir = os.path.dirname(config.LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # フォーマッタの作成
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # ファイルハンドラの設定
    file_handler = RotatingFileHandler(
        config.LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # コンソールハンドラの設定（デバッグモードの場合のみ）
    if config.DEBUG:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 特定のモジュールのログレベル設定
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)

    logging.info(f"Logging initialized with level: {config.LOG_LEVEL}")

    return root_logger
