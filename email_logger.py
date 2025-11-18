import logging
import os
from datetime import datetime


def setup_email_logging():
    """設定郵件客戶端專用日誌"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_filename = "logs/email_client.log"

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 檔案處理器（寫入檔案）
    file_handler = logging.FileHandler(log_filename, encoding='utf-8', mode='a')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # 控制台處理器（只顯示重要訊息）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # 控制台只顯示 INFO 及以上級別

    # 建立 logger
    logger = logging.getLogger('email_client')
    logger.setLevel(logging.DEBUG)  # 檔案記錄所有級別
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 避免重複記錄
    logger.propagate = False

    return logger


# 初始化日誌
email_logger = setup_email_logging()
