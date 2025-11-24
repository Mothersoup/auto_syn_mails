import email
from datetime import datetime, timedelta
from email.header import decode_header
from email.mime.text import MIMEText
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from email.utils import parsedate_to_datetime
from emailClient import MailClient


class EmailProcessor:
    """郵件處理器 - 負責郵件的取得、解析和處理"""

    def __init__(self, mail_client: MailClient):
        self.mail_client = mail_client
        self.logger = mail_client.logger
        # 🎯 過濾條件設定
        self.filter_config = {
            'skip_forwarded': True,  # 跳過已轉發的郵件
            'skip_keywords': ['Fwd:', 'FW:', '轉寄:', '自動轉發'],
            'clean_subject_prefixes': [  # 要清理的主旨前綴
                'Fwd:',
                'FW:',
                '轉寄:',
                '[自動轉發]',
                'Re:',
                '回覆:',
                '(SPAM)'
            ]
        }

    def get_email_list(self, limit: int = 50,
                       range_date: Optional[dict] = None,
                       range_time: Optional[int] = None
                       ) -> list[dict]:
        """取得郵件列表 - 根據可用協定"""
        if not self.mail_client.can_receive_email():
            print("❌ 沒有可用的收信協定")
            return []

        receive_protocol = self.mail_client.get_receive_protocol()

        if receive_protocol in ['pop3', 'imap']:
            return self.get_emails_generic(receive_protocol, limit, range_date, range_time)
        else:
            return []

    def get_emails_generic(self, protocol: str, limit: int = -1,
                           range_date: Optional[dict] = None,
                           range_time: Optional[int] = None) -> list[dict]:
        """通用方法取得郵件列表"""
        try:
            # 參數驗證
            if range_date is not None and range_time is not None:
                raise ValueError("❌ range_date 和 range_time 只能使用一個")

            # 設定時間範圍
            current_time = datetime.now()
            if range_date is None and range_time is None:
                # 預設取得最近24小時的郵件
                time_range = {
                    'start': (current_time - timedelta(hours=24)),
                    'end': current_time
                }
            elif range_time is not None:
                # 使用小時數計算時間範圍
                time_range = {
                    'start': (current_time - timedelta(hours=range_time)),
                    'end': current_time
                }
            else:
                # 使用提供的 range_date
                time_range = range_date

            print(
                f"📧 搜尋條件 - 協定: {protocol}, 數量: {limit}, 時間範圍: {time_range['start']} 到 {time_range['end']}")

            # 確保伺服器連線
            if not self._ensure_server_connection(protocol):
                print(f"❌ {protocol.upper()} 伺服器連線失敗")
                return []

            # 取得郵件列表
            email_ids = self._get_email_ids(protocol)
            if not email_ids:
                print(f"❌ 取得 {protocol.upper()} 郵件列表失敗  function_name : {self.get_emails_generic.__name__} ")
                return []

            # 解析時間範圍
            start_time = time_range['start']
            end_time = time_range['end']

            if not start_time or not end_time:
                print("❌ 時間範圍格式錯誤")
                return []

            # 根據時間範圍篩選郵件
            recent_emails = []
            email_count = 0
            start = False
            for email_id in reversed(email_ids):
                email_data = self._fetch_email_data(protocol=protocol, email_id=email_id)
                print("_______________________________________________", email_data['date'], "-----",
                      type(email_data['date']))
                email_date = parsedate_to_datetime(email_data['date'])
                print("===============================================", email_date, "-----", type(email_date))
                if start_time <= EmailProcessor._parse_datetime(email_date) <= end_time:
                    start = True
                    recent_emails.append(email_data)
                    email_count += 1
                    if limit != -1 and len(recent_emails) >= limit:
                        break
                elif start:
                    # 已經超出時間範圍，停止搜尋
                    break

            print(f"✅ 找到 {len(recent_emails)} 封符合條件的郵件")
            return recent_emails

        except Exception as e:
            print(f"❌ {protocol.upper()} 取得郵件列表失敗: {e} : function_name {self.get_emails_generic.__name__}")
            return []

    def _ensure_server_connection(self, protocol: str) -> bool:
        """確保伺服器連線正常"""
        try:
            if protocol == 'pop3':
                if not self.mail_client.pop3_server:
                    self.mail_client.connect_pop3_connection(self.mail_client.pop3_config)
                return self.mail_client.pop3_server is not None

            elif protocol == 'imap':
                if not self.mail_client.imap_server:
                    self.mail_client.connect_imap_connection(self.mail_client.imap_config)
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

                try:
                    # 添加環境偵錯資訊
                    pop3_status, messages, octets = self.mail_client.pop3_server.list()
                except Exception as e:
                    print(f"❌ POP3 LIST 命令失敗: {e} function_name : {self._get_email_ids.__name__} ")
                    return []
                if pop3_status.startswith(b'+OK'):
                    email_ids = []
                    for msg_info in messages:
                        parts = msg_info.decode().split()
                        if parts:
                            email_ids.append(parts[0])
                    self.mail_client.pop3_server.top(1, 20)  # 測試 RETR 命令
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

    def _fetch_email_data_via_pop3(self, email_id: str) -> Optional[dict]:
        """透過 POP3 取得單一郵件內容"""
        try:
            print(f"    🔍 取得 POP3 郵件 {email_id} 內容...")
            pop3_status, msg_lines, octets = self.mail_client.pop3_server.retr(int(email_id))

            if not pop3_status.startswith(b'+OK') or not msg_lines:
                print(f"    ❌ 取得 POP3 郵件 {email_id} 失敗")
                return None

            email_body = b'\r\n'.join(msg_lines)
            email_message = email.message_from_bytes(email_body)
            return EmailProcessor.parse_email_message(email_message, email_id)

        except Exception as e:

            if 'line too long' in str(e):

                print("檢測到長行問題，嘗試修復...")

                return self._retry_with_larger_buffer(email_id)

            else:

                raise e

    def _fetch_email_data_via_imap(self, email_id) -> Optional[dict]:
        """透過 IMAP 取得單一郵件內容"""
        try:
            status, msg_data = self.mail_client.imap_server.fetch(email_id, '(RFC822)')

            if status != 'OK' or not msg_data or not msg_data[0]:
                print(f"    ❌ 取得 IMAP 郵件 {email_id} 失敗")
                return None

            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            return EmailProcessor.parse_email_message(email_message, email_id)

        except Exception as e:
            print(f"    ❌ 解析 IMAP 郵件 {email_id} 失敗: {e}")
            return None

    @staticmethod
    def parse_email_message(email_message, email_id):
        """解析郵件訊息"""
        try:
            # 取得標頭資訊並解碼

            # 使用解碼函數
            subject = EmailProcessor.decode_header(email_message.get('Subject', ''))
            from_ = EmailProcessor.decode_header(email_message.get('From', ''))
            to = EmailProcessor.decode_header(email_message.get('To', ''))
            date = email_message.get('Date', '')
            # 2. 從 Received 標頭提取
            received_headers = email_message.get_all('Received', [])
            for received in reversed(received_headers):
                try:
                    if ';' in received:
                        date_part = received.split(';')[-1].strip()
                        date = date_part
                        break
                except:
                    continue

            print(f"🔍 解析結果 - 主題: {subject}, 日期: {date}")

            # 解析郵件內容（保持不變）
            body_text = ""
            body_html = ""

            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))

                    if 'attachment' in content_disposition:
                        continue

                    if content_type == 'text/plain' and not body_text:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body_text = payload.decode('utf-8', errors='ignore')
                        except:
                            pass
                    elif content_type == 'text/html' and not body_html:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body_html = payload.decode('utf-8', errors='ignore')
                        except:
                            pass
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
                'subject': subject,  # 現在是字串了！
                'from': from_,  # 現在是字串了！
                'to': to,  # 現在是字串了！
                'date': date,
                'body_text': body_text,
                'body_html': body_html,
                'attachments': []
            }

        except Exception as e:
            print(f"    ❌ 解析郵件內容失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def should_skip_email(self, email_data: dict) -> bool:
        """檢查是否應該跳過這封郵件"""
        try:
            # 🎯 先清理主旨，然後用清理後的主旨來檢查
            original_subject = email_data.get('subject', '')
            clean_subject = self.clean_email_subject(original_subject)

            # 1. 檢查是否為已轉發郵件（使用清理後的主旨）
            if self.filter_config['skip_forwarded']:
                for keyword in self.filter_config['skip_keywords']:
                    if keyword.lower() in clean_subject.lower():
                        print(f"⏭️  跳過已轉發郵件: {original_subject[:30]}... -> {clean_subject[:30]}...")
                        return True

            # 2. 其他過濾條件...
            return False

        except Exception as e:
            print(f"❌ 過濾郵件時出錯: {e}")
            return False

    def clean_email_subject(self, subject: str) -> str:
        """清理郵件主旨，遞歸移除重複的前綴"""
        try:
            if not subject:
                return subject

            original_subject = subject
            prefixes = self.filter_config['clean_subject_prefixes']

            # 🎯 遞歸移除所有前綴
            while True:
                subject_stripped = subject.strip()
                removed_any = False

                for prefix in prefixes:
                    # 檢查是否有前綴（不區分大小寫）
                    if subject_stripped.lower().startswith(prefix.lower()):
                        # 移除前綴並繼續檢查
                        subject = subject_stripped[len(prefix):].strip()
                        removed_any = True
                        print(f"   🔄 移除前綴: '{prefix}' → 剩餘: '{subject}'")
                        break  # 跳出 for 循環，重新檢查所有前綴

                # 如果沒有移除任何前綴，就結束
                if not removed_any:
                    break

            if original_subject != subject:
                print(f"   🧹 主旨清理: '{original_subject}' → '{subject}'")

            return subject

        except Exception as e:
            print(f"❌ 清理主旨時出錯: {e}")
            return subject

    def process_email_for_forwarding(self, email_data: dict) -> dict:
        """處理郵件以準備轉發"""
        try:
            # 深層複製郵件數據，避免修改原始數據
            processed_email = email_data.copy()

            # 1. 清理主旨
            processed_email['original_subject'] = processed_email.get('subject', '')  # 保存原始主旨
            processed_email['subject'] = self.clean_email_subject(processed_email['subject'])

            # 2. 添加處理標記
            processed_email['processed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            processed_email['processed_by'] = 'auto_forward_bot'

            return processed_email

        except Exception as e:
            print(f"❌ 處理郵件時出錯: {e}")
            return email_data

    def forward_email_with_filter(self, email_data, target_emails: list):
        """帶有過濾條件的轉發郵件"""
        try:
            if not isinstance(target_emails, list):
                target_emails = [target_emails]

            # 🎯 處理郵件（清理主旨等）
            processed_email = self.process_email_for_forwarding(email_data)

            # 🎯 建立轉發郵件內容（使用清理後的主旨）
            forward_content = self._create_forward_content(processed_email)

            # 🎯 發送轉發郵件
            self._send_forwarded_email(
                to_emails=target_emails,
                subject=forward_content['subject'],
                body=forward_content['body']
            )

            print(f"  ✅ 已轉發: {processed_email['subject'][:30]}...")
            return True

        except Exception as e:
            print(f"  ❌ 轉發失敗: {e}")
            return False

    def forward_email(self, email_data, target_emails: list):
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

        # 選擇您喜歡的主旨格式
        subject = f"[自動轉發]{email_data['subject']}"

        # 建立專業的轉發內文
        body = f"""
    自動轉發通知 - 郵件摘要
    ─────────────────────────────────────

    📋 原始郵件資訊：
    • 主旨：{email_data['subject']}
    • 寄件者：{email_data['from']}
    • 原始收件者：{email_data['to']}
    • 發送時間：{email_data['date']}

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

    @staticmethod
    def decode_header(header):
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
        except Exception as e:
            print(e)
            return header

    def _send_forwarded_email(self, to_emails, subject, body, attachments=None):
        """發送轉發郵件"""
        """發送轉發郵件"""
        try:
            # 確保 to_emails 是列表
            if not isinstance(to_emails, list):
                to_emails = [to_emails]

            # 確保 SMTP 連線
            if not self.mail_client.smtp_server:
                print("🔌 連接 SMTP 伺服器...")
                self.mail_client.connect_smtp_connection(self.mail_client.smtp_config)

            if not self.mail_client.smtp_server:
                raise Exception("SMTP 伺服器連接失敗")

            # 建立郵件
            msg = MIMEMultipart()
            msg['From'] = f"AutoForwarding Bot <{self.mail_client.account['email']}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"Fwd: {subject}"
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # 添加郵件正文
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 添加附件
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, 'rb') as file:
                            attachment = MIMEApplication(file.read(), Name=os.path.basename(attachment_path))
                        attachment[
                            'Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                        msg.attach(attachment)
                    else:
                        print(f"⚠️ 附件不存在: {attachment_path}")

            # 發送郵件
            print(f"📤 發送轉發郵件到: {', '.join(to_emails)}")
            self.mail_client.smtp_server.send_message(msg)
            print(f"✅ 轉發郵件發送成功")

            return True

        except Exception as e:
            print(f"❌ 發送轉發郵件失敗: {e}")
            return False

    def _get_emails_via_pop3(self, limit: int) -> list[dict]:
        """透過 POP3 取得郵件列表"""
        try:
            if not self.mail_client.pop3_server:
                self.mail_client.connect_pop3_connection(self.mail_client.pop3_config)
            pop3_status, messages, octets = self.mail_client.pop3_server.list()

            if pop3_status.startswith(b'+OK'):
                email_ids = []
                for msg_info in messages:
                    parts = msg_info.decode().split()
                    if parts:
                        email_ids.append(parts[0])

                recent_emails = []
                for email_id in email_ids:
                    email_data = self._fetch_email_data_via_pop3(email_id)
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
            if not self.mail_client.imap_server:
                self.mail_client.connect_imap_connection(self.mail_client.imap_config)

            self.mail_client.imap_server.select('inbox')
            status, messages = self.mail_client.imap_server.search(None, 'ALL')

            if status == 'OK':
                email_ids = messages[0].split()
                recent_emails = []
                for email_id in email_ids[-limit:]:
                    email_data = self._fetch_email_data_via_imap(email_id)
                    if email_data:
                        recent_emails.append(email_data)
                return recent_emails
            else:
                print("❌ 取得 IMAP 郵件列表失敗")
                return []

        except Exception as e:
            print(f"❌ IMAP 取得郵件列表失敗: {e}")
            return []

    @staticmethod
    def _parse_datetime(datetime_str):
        """解析日期輸入 - 支援字串和 datetime 物件"""
        if not datetime_str:
            return None

        # 如果已經是 datetime 物件，直接處理
        if isinstance(datetime_str, datetime):
            # 轉為時區無知
            if datetime_str.tzinfo is not None:
                return datetime_str.astimezone().replace(tzinfo=None)
            else:
                return datetime_str

        # 如果是字串，進行解析
        elif isinstance(datetime_str, str):
            try:
                from email.utils import parsedate_to_datetime
                result = parsedate_to_datetime(datetime_str)

                # 轉為時區無知
                if result and result.tzinfo is not None:
                    return result.astimezone().replace(tzinfo=None)
                return result

            except Exception as e:
                print(f"   ❌ 日期解析失敗: '{datetime_str}' - {e}")
                return None
        else:
            print(f"   ❌ 不支援的日期類型: {type(datetime_str)}")
            return None

    def _retry_with_larger_buffer(self, email_id):
        """使用更大的緩衝區重試"""
        import poplib

        # 保存原始值
        original_maxline = getattr(poplib, '_MAXLINE', 2048)

        try:
            # 暫時增加限制
            poplib._MAXLINE = 1048576  # 1MB
            if hasattr(self.mail_client.pop3_server, '_maxline'):
                self.mail_client.pop3_server._maxline = 1048576

            response, msg_lines, octets = self.mail_client.pop3_server.retr(int(email_id))

            email_body = b'\r\n'.join(msg_lines)
            email_message = email.message_from_bytes(email_body)
            return EmailProcessor.parse_email_message(email_message, email_id)

        finally:
            # 恢復原始設置
            poplib._MAXLINE = original_maxline

    def debug_pop3_connection_state(self):
        """詳細檢查 POP3 連接狀態"""
        try:
            print("\n🔍 === POP3 連接狀態詳細檢查 ===")

            server = self.mail_client.pop3_server

            # 1. 檢查基本命令
            print("1. 測試基本命令:")
            try:
                noop_response = server.noop()
                print(f"   ✅ NOOP: {noop_response}")
            except Exception as e:
                print(f"   ❌ NOOP 失敗: {e}")
                return False

            # 2. 測試 STAT 命令
            print("2. 測試 STAT 命令:")
            try:
                count, size = server.stat()
                print(f"   ✅ STAT: {count} 郵件, {size} bytes")
            except Exception as e:
                print(f"   ❌ STAT 失敗: {e}")
                return False

            # 3. 修正 LIST 命令測試
            print("3. 修正 LIST 命令測試:")
            try:
                # 使用正常的 list() 方法
                pop3_status, messages, octets = server.list()
                print(f"   LIST 狀態: {pop3_status}")
                print(f"   消息數量: {len(messages)}")
                print(f"   數據大小: {octets} bytes")

                if pop3_status.startswith(b'+OK'):
                    print("   ✅ LIST 命令成功")
                    # 顯示前幾個郵件項目
                    for i, msg in enumerate(messages[:3]):
                        print(f"     郵件 {i + 1}: {msg.decode('utf-8', errors='ignore')}")
                    return True
                else:
                    print(f"   ❌ LIST 響應異常: {pop3_status}")
                    return False

            except Exception as e:
                print(f"   ❌ LIST 測試失敗: {e}")
                return False

        except Exception as e:
            print(f"❌ 連接狀態檢查失敗: {e}")
            return False
