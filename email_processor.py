import email
from datetime import datetime
from email.header import decode_header
from typing import Optional

from emailClient import MailClient
from json_reader import MailReaders


class EmailProcessor:
    """郵件處理器 - 負責郵件的取得、解析和處理"""

    def __init__(self, mail_client):
        self.mail_client = mail_client
        self.logger = mail_client.logger

    def get_email_list(self, limit: int = 10) -> list[dict]:
        """取得郵件列表 - 根據可用協定"""
        if not self.mail_client.can_receive_email():
            print("❌ 沒有可用的收信協定")
            return []

        receive_protocol = self.mail_client.get_receive_protocol()

        if receive_protocol in ['pop3', 'imap']:
            return self._get_emails_generic(receive_protocol, limit)
        else:
            return []

    def _get_emails_generic(self, protocol: str, limit: int) -> list[dict]:
        """通用方法取得郵件列表"""
        try:
            # 確保伺服器連線
            if not self._ensure_server_connection(protocol):
                print(f"❌ {protocol.upper()} 伺服器連線失敗")
                return []

            # 取得郵件列表
            email_ids = self._get_email_ids(protocol)
            if not email_ids:
                print(f"❌ 取得 {protocol.upper()} 郵件列表失敗")
                return []

            # 取得郵件內容
            recent_emails = []
            for email_id in email_ids[-limit:]:
                email_data = self._fetch_email_data(protocol, email_id)
                if email_data:
                    recent_emails.append(email_data)

            return recent_emails

        except Exception as e:
            print(f"❌ {protocol.upper()} 取得郵件列表失敗: {e}")
            return []

    def _ensure_server_connection(self, protocol: str) -> bool:
        """確保伺服器連線正常"""
        try:
            if protocol == 'pop3':
                if not self.mail_client.pop3_server:
                    self.mail_client._connect_pop3_connection(self.mail_client.pop3_config)
                return self.mail_client.pop3_server is not None

            elif protocol == 'imap':
                if not self.mail_client.imap_server:
                    self.mail_client._connect_imap_connection(self.mail_client.imap_config)
                if self.mail_client.imap_server:
                    self.mail_client.imap_server.select('inbox')
                    return True
                return False

            return False
        except Exception as e:
            print(f"❌ {protocol.upper()} 伺服器連線錯誤: {e}")
            return False

    def _get_email_ids(self, protocol: str) -> list:
        """根據協定取得郵件 ID 列表"""
        try:
            if protocol == 'pop3':
                pop3_status, messages, octets = self.mail_client.pop3_server.list()
                if pop3_status.startswith(b'+OK'):
                    email_ids = []
                    for msg_info in messages:
                        parts = msg_info.decode().split()
                        if parts:
                            email_ids.append(parts[0])
                    return email_ids

            elif protocol == 'imap':
                status, messages = self.mail_client.imap_server.search(None, 'ALL')
                if status == 'OK':
                    return messages[0].split()

            return []
        except Exception as e:
            print(f"❌ 取得 {protocol.upper()} 郵件 ID 失敗: {e}")
            return []

    def _fetch_email_data(self, protocol: str, email_id) -> Optional[dict]:
        """根據協定取得單一郵件內容"""
        if protocol == 'pop3':
            return self._fetch_email_data_via_pop3(email_id)
        elif protocol == 'imap':
            return self._fetch_email_data_via_imap(email_id)
        return None

    def _fetch_email_data_via_pop3(self, email_id) -> Optional[dict]:
        """透過 POP3 取得單一郵件內容"""
        try:
            pop3_status, msg_lines, octets = self.mail_client.pop3_server.retr(email_id)

            if not pop3_status.startswith(b'+OK') or not msg_lines:
                print(f"    ❌ 取得 POP3 郵件 {email_id} 失敗")
                return None

            email_body = b'\r\n'.join(msg_lines)
            email_message = email.message_from_bytes(email_body)
            return self._parse_email_message(email_message, email_id)

        except Exception as e:
            print(f"    ❌ 解析 POP3 郵件 {email_id} 失敗: {e}")
            return None

    def _fetch_email_data_via_imap(self, email_id) -> Optional[dict]:
        """透過 IMAP 取得單一郵件內容"""
        try:
            status, msg_data = self.mail_client.imap_server.fetch(email_id, '(RFC822)')

            if status != 'OK' or not msg_data or not msg_data[0]:
                print(f"    ❌ 取得 IMAP 郵件 {email_id} 失敗")
                return None

            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            return self._parse_email_message(email_message, email_id)

        except Exception as e:
            print(f"    ❌ 解析 IMAP 郵件 {email_id} 失敗: {e}")
            return None

    def _parse_email_message(self, email_message, email_id):
        """解析郵件訊息"""
        try:
            # 取得標頭資訊
            subject = self._decode_header(email_message.get('Subject', ''))
            from_ = self._decode_header(email_message.get('From', ''))
            to = self._decode_header(email_message.get('To', ''))
            date = email_message.get('Date', '')

            # 解析郵件內容
            body_text = ""
            body_html = ""

            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))

                    # 跳過附件
                    if 'attachment' in content_disposition:
                        continue

                    if content_type == 'text/plain' and not body_text:
                        body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif content_type == 'text/html' and not body_html:
                        body_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                # 單一部分郵件
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
                'attachments': []  # POP3 通常不處理附件下載
            }

        except Exception as e:
            print(f"    ❌ 解析郵件內容失敗: {e}")
            return None

    def forward_email(self, email_data, target_emails):
        """轉發郵件到指定地址"""
        try:
            if not isinstance(target_emails, list):
                target_emails = [target_emails]

            # 建立轉發郵件內容
            forward_content = self._create_forward_content(email_data)

            # 發送轉發郵件
            self._send_forwarded_email(
                to_emails=target_emails,
                subject=forward_content['subject'],
                body=forward_content['body']
            )

            print(f"  ✅ 已轉發: {email_data['subject'][:30]}...")

        except Exception as e:
            print(f"  ❌ 轉發失敗: {e}")

    def _create_forward_content(self, email_data):
        """建立轉發郵件內容"""
        source_account = self.mail_client.account['name']

        # 選擇您喜歡的主旨格式
        subject = f"[自動轉發][{source_account}] {email_data['subject']}"

        # 建立專業的轉發內文
        body = f"""
    自動轉發通知 - 郵件摘要
    ─────────────────────────────────────

    📋 原始郵件資訊：
    • 主旨：{email_data['subject']}
    • 寄件者：{email_data['from']}
    • 原始收件者：{email_data['to']}
    • 發送時間：{email_data['date']}
    • 來源帳號：{source_account}

    ─────────────────────────────────────
    📝 郵件內容：
    {email_data['body_text']}

    ─────────────────────────────────────
    🤖 此為自動轉發郵件
    發送者：auto_forward_bot
    轉發時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    ─────────────────────────────────────
    """

        return {
            'subject': subject,
            'body': body
        }

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


def main():
    jason_reader_instance = MailReaders()
    clients_dict = jason_reader_instance.load_accounts()
    clients = [MailClient(account_info) for account_info in clients_dict]
    operators_for_clients = [EmailProcessor(client) for client in clients]
    # store multiple mail to check mail
    unique_mail = []
    seen_subjects = set()
    for operator in operators_for_clients:
        print(f"\n=== 帳號: {operator.mail_client.account['name']} ===")
        print(f"可用協定: {operator.mail_client.get_available_protocols()}")
        print(f"收信協定: {operator.mail_client.get_receive_protocol()}")
        print("\n取得最近 10 封郵件:")
        for e in operator.get_email_list(limit=10):
            if e['subject'] not in seen_subjects:
                seen_subjects.add(e['subject'])
                e['from'] = "auto_forward_bot"
                unique_mail.append(e)
            print(f"  主旨: {e['subject']}")
            print(f"  寄件者: {e['from']}")
            print(f"  收件者: {e['to']}")
            print(f"  日期: {e['date']}")
            print(f"  內容預覽: {e['body_text'][:50]}...\n")
    print("\n=== 統整所有帳號的唯一郵件清單 ===")
    print(len(unique_mail))

    for operator in operators_for_clients:
        for e in operator.get_email_list(limit=10):


if __name__ == "__main__":
    main()
