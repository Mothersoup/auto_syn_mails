import json
import os
from datetime import datetime, timedelta
from functools import singledispatchmethod

class DateConfigManager:
    def __init__(self, config_path="date.json"):
        self.config_path = config_path
        self.config = self.__load_config()



    def __write_syn_time(self,emails:list[dict] = None  , range_date : dict | int = None):
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
    @singledispatchmethod
    def __write_syn_time(self,emails:list[dict] = None  , range_hours : int = None):
