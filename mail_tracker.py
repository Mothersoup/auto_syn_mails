import json
import os
from datetime import datetime


class ForwardTracker:
    def __init__(self, tracker_file="forward_tracker.json"):
        self.tracker_file = tracker_file
        self.forwarded_emails = self.load_tracked_emails()

    def load_tracked_emails(self):
        """載入已轉發的郵件記錄"""
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_tracked_emails(self):
        """儲存轉發記錄"""
        try:
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump(self.forwarded_emails, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 儲存追蹤記錄失敗: {e}")
            return False

    def is_email_forwarded(self, email_data):
        """檢查郵件是否已經轉發過"""
        email_id = self._generate_email_id(email_data)
        return email_id in self.forwarded_emails

    def mark_email_forwarded(self, email_data):
        """標記郵件為已轉發"""
        email_id = self._generate_email_id(email_data)
        self.forwarded_emails[email_id] = {
            'subject': email_data['subject'],
            'from': email_data['from'],
            'date': email_data['date'],
            'source_account': email_data.get('source_account', 'unknown'),
            'forwarded_at': datetime.now().isoformat()
        }
        self.save_tracked_emails()

    def _generate_email_id(self, email_data):
        """為郵件生成唯一ID"""
        import hashlib
        content = f"{email_data['subject']}_{email_data['from']}_{email_data['date']}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()