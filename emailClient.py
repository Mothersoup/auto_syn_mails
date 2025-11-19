import email
from email.header import decode_header
from typing import Optional
from email_logger import email_logger
from connection_manager import ConnectionManager
from mail_reader import auto_load_smtp, auto_load_imap, auto_load_pop3, MailReaders


class MailClient:
    def __init__(self, account_info: dict):
        # 核心帳號資訊
        self.account = {
            'name': account_info['name'],
            'email': account_info['email'],
            'password': account_info['password']
        }

        # 系統組件
        self.logger = email_logger
        self.conn_manager = ConnectionManager(
            self.account['email'],
            self.account['password']
        )

        # 狀態管理
        self._configs = {}
        self._servers = {}
        self._connected = False
        self.available_protocols = []

        # 為了向後兼容，保持原有變數名稱
        self.smtp_server = None
        self.imap_server = None
        self.pop3_server = None
        self.is_connected = False

        # 初始化設定
        self._initialize_configs(account_info)

    def _initialize_configs(self, account_info: dict):
        """初始化所有協定設定"""
        for protocol in ['smtp', 'imap', 'pop3']:
            config = self._resolve_protocol_config(account_info, protocol)
            self._configs[protocol] = config

            # 同步到舊變數（向後兼容）
            if protocol == 'smtp':
                self.smtp_config = config
            elif protocol == 'imap':
                self.imap_config = config
            elif protocol == 'pop3':
                self.pop3_config = config

    # 屬性存取方法
    @property
    def smtp_server(self):
        return self._servers.get('smtp')

    @smtp_server.setter
    def smtp_server(self, value):
        self._servers['smtp'] = value

    @property
    def imap_server(self):
        return self._servers.get('imap')

    @imap_server.setter
    def imap_server(self, value):
        self._servers['imap'] = value

    @property
    def pop3_server(self):
        return self._servers.get('pop3')

    @pop3_server.setter
    def pop3_server(self, value):
        self._servers['pop3'] = value

    @property
    def is_connected(self):
        return self._connected

    @is_connected.setter
    def is_connected(self, value):
        self._connected = value

    # 簡化後的連接方法
    def _connect_smtp_connection(self, config: dict) -> bool:
        """建立 SMTP 連接並登入"""
        self.smtp_server, error = self.conn_manager.connect_protocol(config, 'smtp')
        if error:
            self.smtp_server = None
            raise Exception(error)
        self.available_protocols.append('smtp')
        return True

    def _test_smtp_connection(self, config: dict) -> bool:
        """測試 SMTP 連接是否成功"""
        return self.conn_manager.test_connection(config, 'smtp')

    def _connect_pop3_connection(self, config: dict) -> bool:
        """建立 POP3 連接並登入"""
        self.pop3_server, error = self.conn_manager.connect_protocol(config, 'pop3')
        if error:
            self.pop3_server = None
            raise Exception(error)
        self.available_protocols.append('pop3')
        return True

    def _test_pop3_connection(self, config: dict) -> bool:
        """測試 POP3 連接是否成功"""
        return self.conn_manager.test_connection(config, 'pop3')

    def _connect_imap_connection(self, config: dict) -> bool:
        """建立 IMAP 連接並登入"""
        self.imap_server, error = self.conn_manager.connect_protocol(config, 'imap')
        if error:
            self.imap_server = None
            raise Exception(error)
        self.available_protocols.append('imap')
        return True

    def _test_imap_connection(self, config: dict) -> bool:
        """測試 IMAP 連接是否成功"""
        return self.conn_manager.test_connection(config, 'imap')

    def _auto_detect_protocol(self, protocol: str) -> Optional[dict]:
        """
        通用協定自動偵測方法

        Args:
            protocol: 協定類型 ('smtp', 'imap', 'pop3')

        Returns:
            dict: 偵測到的設定，None 表示偵測失敗
        """
        # 協定配置映射
        protocol_config = {
            'smtp': {
                'load_func': auto_load_smtp,
                'default_ports': [587, 465],
                'test_method': self._test_smtp_connection,
                'ssl_ports': [465]
            },
            'imap': {
                'load_func': auto_load_imap,
                'default_ports': [993, 143],
                'test_method': self._test_imap_connection,
                'ssl_ports': [993]
            },
            'pop3': {
                'load_func': auto_load_pop3,
                'default_ports': [995, 110],
                'test_method': self._test_pop3_connection,
                'ssl_ports': [995]
            }
        }

        if protocol not in protocol_config:
            return None

        config = protocol_config[protocol]
        domain = self.account['email'].split('@')[-1].lower()

        # 載入設定檔
        protocol_configs = config['load_func']()

        # 1. 嘗試已知服務商設定
        known_configs = protocol_configs.get("known_providers", {}).get(domain, [])
        for known_config in known_configs:
            if config['test_method'](known_config):
                success_msg = f"使用已知 {protocol.upper()} 設定: {known_config['server']}:{known_config['port']}"
                print(f"✅ {success_msg}")
                self.logger.info(success_msg)
                if protocol not in self.available_protocols:
                    self.available_protocols.append(protocol)
                return known_config

        # 2. 嘗試伺服器模式組合
        server_patterns = protocol_configs.get("server_patterns", [])
        ports_to_try = protocol_configs.get("ports_to_try", config['default_ports'])

        for pattern in server_patterns:
            server_name = pattern.replace('{domain}', domain)

            for port in ports_to_try:
                use_ssl = (port in config['ssl_ports'])
                test_config = {
                    'server': server_name,
                    'port': port,
                    'ssl': use_ssl
                }

                if config['test_method'](test_config):
                    success_msg = f"使用通用 {protocol.upper()} 設定: {server_name}:{port}"
                    print(f"✅ {success_msg}")
                    self.logger.info(success_msg)
                    # ✅ 新增：將成功連線的協定加入到可用列表
                    if protocol not in self.available_protocols:
                        self.available_protocols.append(protocol)
                    return test_config

        # 偵測失敗，記錄到日誌
        error_msg = f"無法自動偵測 {self.account['email']} 的 {protocol.upper()} 設定"
        print(f"⚠️  {error_msg}")
        self.logger.warning(error_msg)
        return None

    def _resolve_protocol_config(self, account_config: dict, protocol: str) -> Optional[dict]:
        """
        通用協定設定解析方法
        """
        protocol_setting = account_config.get(protocol)

        if protocol_setting == 'auto':
            # 自動偵測
            return self._auto_detect_protocol(protocol)
        elif isinstance(protocol_setting, dict):
            # 使用自訂設定
            return protocol_setting
        elif isinstance(protocol_setting, str) and protocol_setting != 'auto':
            # 簡化格式處理
            defaults = {
                'smtp': (587, False),
                'imap': (993, True),
                'pop3': (995, True)
            }
            port, ssl = defaults.get(protocol, (587, False))
            return {'server': protocol_setting, 'port': port, 'ssl': ssl}
        else:
            # 無效設定，嘗試自動偵測
            self.logger.debug(f"無效的 {protocol.upper()} 設定，嘗試自動偵測")
            return self._auto_detect_protocol(protocol)

    def get_email_list(self, limit: int = 10) -> list[dict]:
        """取得郵件列表 - 根據可用協定"""
        if not self.can_receive_email():
            print("❌ 沒有可用的收信協定")
            return []

        receive_protocol = self.get_receive_protocol()

        if receive_protocol == 'pop3':
            return self._get_emails_via_pop3(limit)
        elif receive_protocol == 'imap':
            return self._get_emails_via_imap(limit)
        else:
            return []

    def _get_emails_via_pop3(self, limit: int) -> list[dict]:
        """透過 POP3 取得郵件列表"""
        try:
            if not self.pop3_server:
                self._connect_pop3_connection(self.pop3_config)

            pop3_status, messages, octets = self.pop3_server.list()

            if pop3_status.startswith(b'+OK'):
                email_ids = []
                for msg_info in messages:
                    parts = msg_info.decode().split()
                    if parts:
                        email_ids.append(parts[0])

                recent_emails = []
                for email_id in email_ids[-limit:]:
                    email_data = self._fetch_email_data_pop3(email_id)
                    if email_data:
                        recent_emails.append(email_data)

                return recent_emails
            else:
                print("❌ 取得 POP3 郵件列表失敗")
                return []

        except Exception as e:
            print(f"❌ POP3 取得郵件列表失敗: {e}")
            return []

    def _get_emails_via_imap(self, limit: int) -> list[dict]:
        """透過 IMAP 取得郵件列表"""
        try:
            if not self.imap_server:
                self._connect_imap_connection(self.imap_config)

            self.imap_server.select('inbox')
            status, messages = self.imap_server.search(None, 'ALL')

            if status == 'OK':
                email_ids = messages[0].split()
                recent_emails = []
                for email_id in email_ids[-limit:]:
                    email_data = self._fetch_email_data_imap(email_id)
                    if email_data:
                        recent_emails.append(email_data)
                return recent_emails
            else:
                print("❌ 取得 IMAP 郵件列表失敗")
                return []

        except Exception as e:
            print(f"❌ IMAP 取得郵件列表失敗: {e}")
            return []

    def _fetch_email_data_pop3(self, email_id):
        """取得單一郵件的完整資料 - POP3 版本"""
        try:
            pop3_status, msg_lines, octets = self.pop3_server.retr(email_id)

            if not pop3_status.startswith(b'+OK') or not msg_lines:
                print(f"    ❌ 取得郵件 {email_id} 失敗")
                return None

            email_body = b'\r\n'.join(msg_lines)
            email_message = email.message_from_bytes(email_body)
            return self._parse_email_message(email_message, email_id)

        except Exception as e:
            print(f"    ❌ 解析郵件 {email_id} 失敗: {e}")
            return None

    def _fetch_email_data_imap(self, email_id):
        """取得單一郵件的完整資料 - IMAP 版本"""
        try:
            status, msg_data = self.imap_server.fetch(email_id, '(RFC822)')

            if status != 'OK' or not msg_data or not msg_data[0]:
                print(f"    ❌ 取得郵件 {email_id} 失敗")
                return None

            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            return self._parse_email_message(email_message, email_id)

        except Exception as e:
            print(f"    ❌ 解析郵件 {email_id} 失敗: {e}")
            return None

    def _parse_email_message(self, email_message, email_id):
        """解析郵件訊息"""
        try:
            subject = self._decode_header(email_message.get('Subject', ''))
            from_ = self._decode_header(email_message.get('From', ''))
            to = self._decode_header(email_message.get('To', ''))
            date = email_message.get('Date', '')

            body_text = ""
            body_html = ""

            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))

                    if 'attachment' in content_disposition:
                        continue

                    if content_type == 'text/plain' and not body_text:
                        body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif content_type == 'text/html' and not body_html:
                        body_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                content_type = email_message.get_content_type()
                payload = email_message.get_payload(decode=True)
                if payload:
                    if content_type == 'text/plain':
                        body_text = payload.decode('utf-8', errors='ignore')
                    elif content_type == 'text/html':
                        body_html = payload.decode('utf-8', errors='ignore')

            return {
                'id': email_id,
                'subject': subject,
                'from': from_,
                'to': to,
                'date': date,
                'body_text': body_text,
                'body_html': body_html,
                'attachments': []
            }

        except Exception as e:
            print(f"    ❌ 解析郵件內容失敗: {e}")
            return None

    def _decode_header(self, header):
        """解碼郵件標頭"""
        try:
            decoded_parts = decode_header(header)
            decoded_str = ''
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_str += part.decode(encoding)
                    else:
                        decoded_str += part.decode('utf-8', errors='ignore')
                else:
                    decoded_str += part
            return decoded_str
        except:
            return header

    # 狀態檢查方法
    def get_available_protocols(self) -> list[str]:
        """取得可用的協定列表"""
        return self.available_protocols

    def can_send_email(self) -> bool:
        """檢查是否可以寄信"""
        return 'smtp' in self.available_protocols

    def can_receive_email(self) -> bool:
        """檢查是否可以收信"""
        return 'imap' in self.available_protocols or 'pop3' in self.available_protocols

    def get_receive_protocol(self) -> Optional[str]:
        """取得收信使用的協定"""
        if 'imap' in self.available_protocols:
            return 'imap'
        elif 'pop3' in self.available_protocols:
            return 'pop3'
        return None

    # 統一管理方法
    def get_config(self, protocol: str) -> Optional[dict]:
        """取得協定設定"""
        return self._configs.get(protocol)

    def get_server(self, protocol: str):
        """取得伺服器連線"""
        return self._servers.get(protocol)

    def set_server(self, protocol: str, server):
        """設定伺服器連線"""
        self._servers[protocol] = server



