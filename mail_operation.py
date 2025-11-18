from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class MailOperation(ABC):
    """郵件操作基礎類別 - 包含共用功能和抽象方法"""

    def __init__(self, email: str, password: str, smtp_config: Dict, imap_config: Dict):
        self.email = email
        self.password = password
        self.smtp_config = smtp_config
        self.imap_config = imap_config
        self.server = None

    # 共用具體方法
    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """發送郵件 - 共用實作"""
        try:
            if not self.server:
                self.connect()

            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            self.server.send_message(msg)
            print(f"✅ 郵件已發送至: {recipient}")
            return True

        except Exception as e:
            print(f"❌ 發送失敗: {e}")
            return False

    # 抽象方法 - 子類必須實作
    @abstractmethod
    def read_emails(self, limit: int = 10) -> List[Dict]:
        """讀取郵件 - 不同服務商實作不同"""
        pass

    @abstractmethod
    def get_folder_list(self) -> List[str]:
        """取得郵件資料夾列表"""
        pass
