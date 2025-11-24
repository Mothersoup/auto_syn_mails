import json
import os
from datetime import datetime, timedelta
from dateutil import parser  # date processing library
import re


class DateConfigManager:
    def __init__(self, config_path="date.json"):
        self.config_path = config_path
        self.config = self.__load_config()

    def __write_syn_time(self, emails: list[dict] = None, range_date: dict | int = None):
        """
        寫入同步時間到 date.json, 同步了哪些mails

        Args:
            emails: 郵件列表
            range_date: 時間範圍（小時），預設 24 小時
        """
        try:
            # 設定預設值
            if emails is None:
                emails = []

            # 計算範圍時間
            current_time = datetime.now()
            # 處理 range_date
            if range_date is None:
                # 預設 24 小時
                range_data = {
                    "start": current_time.isoformat() + "Z",
                    "end": (current_time - timedelta(hours=24)).isoformat() + "Z"
                }
            elif isinstance(range_date, int):
                # 整數處理 - 小時數
                range_data = {
                    "start": current_time.isoformat() + "Z",
                    "end": (current_time - timedelta(hours=range_date)).isoformat() + "Z"
                }
            elif isinstance(range_date, dict):
                # 字典處理 - 直接使用
                range_data = range_date
            else:
                raise TypeError(f"不支援的 range_date 類型: {type(range_date)}")

            # 建立資料結構
            data = {
                "emails": emails,
                "range": {
                    "start": range_data['start'],
                    "end": range_data['end']
                }
            }

            # 寫入檔案
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"✅ 已寫入同步時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   時間範圍: {range_date['start']} to  {range_date['end']}  ")
            print(f"   記錄郵件數量: {len(emails)}")

            return True

        except Exception as e:
            print(f"❌ 寫入同步時間失敗: {e}")
            return False

    def __load_config(self) -> dict:
        """載入設定 - 回傳字典"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print("📭 沒有日期紀錄檔案")
                return {}  # 回傳空字典
        except Exception as e:
            print(f"❌ 載入設定失敗: {e}")
            return {}


class DateInputHandler:
    """智慧日期輸入處理器"""

    @staticmethod
    def parse_date_input(date_input):
        """
        支援多種日期輸入格式：
        - 相對時間: "2 hours ago", "1 day ago", "30 minutes ago"
        - 絕對時間: "2024-01-15", "2024/01/15 14:30"
        - 自然語言: "yesterday", "today", "last week"
        - 時間範圍: "last 24 hours", "past 3 days"
        """
        if not date_input:
            return None

        date_input = str(date_input).strip().lower()

        # 相對時間處理
        relative_result = DateInputHandler._parse_relative_time(date_input)
        if relative_result:
            return relative_result

        # 自然語言處理
        natural_result = DateInputHandler._parse_natural_language(date_input)
        if natural_result:
            return natural_result

        # 絕對時間處理
        try:
            return parser.parse(date_input)
        except:
            raise ValueError(f"無法解析日期格式: {date_input}")

    @staticmethod
    def _parse_relative_time(date_input):
        """解析相對時間"""
        patterns = {
            r'(\d+)\s*hours?\s*ago': 'hours',
            r'(\d+)\s*days?\s*ago': 'days',
            r'(\d+)\s*minutes?\s*ago': 'minutes',
            r'(\d+)\s*weeks?\s*ago': 'weeks',
            r'last\s*(\d+)\s*hours': 'hours',
            r'past\s*(\d+)\s*days': 'days'
        }

        for pattern, unit in patterns.items():
            match = re.search(pattern, date_input)
            if match:
                amount = int(match.group(1))
                if unit == 'hours':
                    return datetime.now() - timedelta(hours=amount)
                elif unit == 'days':
                    return datetime.now() - timedelta(days=amount)
                elif unit == 'minutes':
                    return datetime.now() - timedelta(minutes=amount)
                elif unit == 'weeks':
                    return datetime.now() - timedelta(weeks=amount)
        return None

    @staticmethod
    def _parse_natural_language(date_input):
        """解析自然語言"""
        now = datetime.now()
        mappings = {
            'today': now,
            'yesterday': now - timedelta(days=1),
            'tomorrow': now + timedelta(days=1),
            'now': now,
            'last week': now - timedelta(weeks=1),
            'last month': now - timedelta(days=30)
        }
        return mappings.get(date_input)
