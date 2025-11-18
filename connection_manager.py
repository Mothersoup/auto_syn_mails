import imaplib
import poplib
import smtplib
from email_logger import email_logger


class ConnectionManager:
    """通用的郵件伺服器連接管理器"""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.timeout = 10
        self.logger = email_logger

    def connect_protocol(self, config: dict, protocol: str) -> tuple:
        """
        通用連接方法
        """
        try:
            server_name = config['server']
            port = config['port']
            use_ssl = config.get('ssl', False)

            # 記錄連線嘗試到日誌
            self.logger.info(f"嘗試連接 {protocol.upper()} {server_name}:{port} (SSL: {use_ssl})")

            # 根據協定設定預設 SSL
            if protocol == 'pop3' and use_ssl is None:
                use_ssl = (port == 995)
            elif protocol == 'imap' and use_ssl is None:
                use_ssl = (port == 993)
            elif protocol == 'smtp' and use_ssl is None:
                use_ssl = (port == 465)

            connection = None

            if protocol == 'smtp':
                if use_ssl:
                    connection = smtplib.SMTP_SSL(server_name, port, timeout=self.timeout)
                else:
                    connection = smtplib.SMTP(server_name, port, timeout=self.timeout)
                    connection.starttls()
                connection.login(self.email, self.password)

            elif protocol == 'pop3':
                if use_ssl:
                    connection = poplib.POP3_SSL(server_name, port, timeout=self.timeout)
                else:
                    connection = poplib.POP3(server_name, port, timeout=self.timeout)
                connection.user(self.email)
                connection.pass_(self.password)

            elif protocol == 'imap':
                if use_ssl:
                    connection = imaplib.IMAP4_SSL(server_name, port, timeout=self.timeout)
                else:
                    connection = imaplib.IMAP4(server_name, port, timeout=self.timeout)
                connection.login(self.email, self.password)

            else:
                self.logger.error(f"不支援的協定: {protocol}")
                return None, f"不支援的協定: {protocol}"

            self.logger.info(f"{protocol.upper()} 連接成功: {server_name}:{port}")
            return connection, None

        except Exception as e:
            self.logger.warning(f"{protocol.upper()} 連接失敗 {config['server']}:{config['port']} - {str(e)}")
            return None, str(e)

    def test_connection(self, config: dict, protocol: str) -> bool:
        """
        測試連接是否成功 - 同時記錄到日誌和控制台
        """
        connection, error = self.connect_protocol(config, protocol)

        if error:
            self._handle_connection_error(protocol, error, config)
            return False

        try:
            # 協定特定的測試
            if protocol == 'smtp':
                connection.quit()
                success_msg = f"SMTP 連接成功！ {config['server']}:{config['port']}"
                print(f"✅ {success_msg}")
                self.logger.info(success_msg)

            elif protocol == 'pop3':
                count, size = connection.stat()
                success_msg = f"POP3 連接成功！ {config['server']}:{config['port']} - 共有 {count} 封郵件"
                print(f"✅ {success_msg}")
                self.logger.info(success_msg)
                connection.quit()

            elif protocol == 'imap':
                connection.select('inbox')
                success_msg = f"IMAP 連接成功！ {config['server']}:{config['port']}"
                print(f"✅ {success_msg}")
                self.logger.info(success_msg)
                return True

            return True

        except Exception as e:
            self._handle_connection_error(protocol, str(e), config)
            return False
        finally:
            if protocol != 'imap' and connection:
                try:
                    if protocol == 'smtp':
                        connection.quit()
                    elif protocol == 'pop3':
                        connection.quit()
                except:
                    pass

    def _handle_connection_error(self, protocol: str, error: str, config: dict = None):
        """處理連接錯誤 - 記錄到日誌"""
        server_info = f"{config['server']}:{config['port']}" if config else ""
        error_msg = f"{protocol.upper()} 連接失敗 {server_info}: {error}"
        self.logger.warning(error_msg)
