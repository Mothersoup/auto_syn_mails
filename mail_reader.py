import json
import os
from typing import List, Dict


class MailReaders:
    def __init__(self, config_file: str = "email_accounts.json", ):
        self.config_file = config_file

    def load_accounts(self) -> List[Dict]:
        try:
            if not os.path.exists(self.config_file):
                self._create_json_default()
                return []
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                accounts = data.get("accounts", [])
                print(f"✅ 成功載入 {len(accounts)} 個帳號")
                return accounts
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            return []

    def _create_json_default(self):
        print("📄 未找到設定檔，已建立範例 email_accounts.json")
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump('', f, indent=2, ensure_ascii=False)

    def search_account_by_name(self, name: str) -> Dict:
        accounts = self.load_accounts()
        for account in accounts:
            if account['name'] == name:
                return account
        print(f"⚠️ 未找到名稱為 {name} 的帳號")
        return {}

    def search_account_by_gmail(self, email: str) -> Dict:
        accounts = self.load_accounts()
        for account in accounts:
            if account['email'] == email:
                return account
        print(f"⚠️ 未找到名稱為 {email} 的帳號")
        return {}

    def show_accounts(self):
        accounts = self.load_accounts()
        if not accounts:
            print("⚠️ 沒有可用的帳號")
            return
        print(f"\n📧 找到 {len(accounts)} 個帳號:")
        for i, account in enumerate(accounts, 1):
            print(f"{i}. {account['name']}")
            print(f"   郵件: {account['email']}")
            print(f"   密碼: {'*' * len(account['password'])}")
            print(f"   SMTP: {account['smtp']}")
            print(f"   POP3: {account['pop3']}\n")


def _create_default_smtp_config(config_file):
    default_config = {
        "known_providers": {
            "gmail.com": [
                {
                    "server": "smtp.gmail.com",
                    "port": 587,
                    "ssl": False
                },
                {
                    "server": "smtp.gmail.com",
                    "port": 465,
                    "ssl": True
                }
            ],
            "outlook.com": [
                {
                    "server": "smtp-mail.outlook.com",
                    "port": 587,
                    "ssl": False
                }
            ],
            "yahoo.com": [
                {
                    "server": "smtp.mail.yahoo.com",
                    "port": 587,
                    "ssl": False
                }
            ],
            "cycu.edu.tw": [
                {
                    "server": "smtp.cycu.edu.tw",
                    "port": 465,
                    "ssl": True
                }
            ]
        },
        "server_patterns": [
            "smtp.{domain}",
            "mail.{domain}",
            "smtp01.{domain}",
            "email.{domain}"
        ],
        "ports_to_try": [
            587,
            465,
            25
        ]
    }
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        print(f"💾 建立預設設定檔: {config_file}")
    except Exception as e:
        print(f"⚠️ 無法儲存: {e}")

    return default_config


def _create_default_pop3_config(config_file):
    default_config = {
        "known_providers": {
            "gmail.com": [
                {
                    "server": "pop.gmail.com",
                    "port": 995,
                    "ssl": True
                }
            ],
            "outlook.com": [
                {
                    "server": "outlook.office365.com",
                    "port": 995,
                    "ssl": True
                }
            ],
            "yahoo.com": [
                {
                    "server": "pop.mail.yahoo.com",
                    "port": 995,
                    "ssl": True
                }
            ],
            "hotmail.com": [
                {
                    "server": "outlook.office365.com",
                    "port": 995,
                    "ssl": True
                }
            ],
            "cycu.edu.tw": [
                {
                    "server": "mail.cycu.edu.tw",
                    "port": 110,
                    "ssl": False
                },
                {
                    "server": "mail.cycu.edu.tw",
                    "port": 995,
                    "ssl": True
                }
            ],
            "qq.com": [
                {
                    "server": "pop.qq.com",
                    "port": 995,
                    "ssl": True
                }
            ],
            "163.com": [
                {
                    "server": "pop.163.com",
                    "port": 995,
                    "ssl": True
                }
            ],
            "126.com": [
                {
                    "server": "pop.126.com",
                    "port": 995,
                    "ssl": True
                }
            ],
            "aol.com": [
                {
                    "server": "pop.aol.com",
                    "port": 995,
                    "ssl": True
                }
            ],
            "icloud.com": [
                {
                    "server": "pop.mail.me.com",
                    "port": 995,
                    "ssl": True
                }
            ]
        },
        "server_patterns": [
            "pop.{domain}",
            "pop3.{domain}",
            "mail.{domain}",
            "pop.{domain}.com",
            "pop3.{domain}.com",
            "mail.{domain}.com",
            "pop01.{domain}",
            "pop02.{domain}",
            "pop-mail.{domain}",
            "pop3-mail.{domain}"
        ],
        "ports_to_try": [
            995,
            110
        ],
        "timeout_settings": {
            "connection_timeout": 10,
            "read_timeout": 30
        },
        "pop3_features": {
            "support_uidl": True,
            "support_top": True,
            "leave_messages_on_server": True
        }
    }
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        print(f"💾 建立預設 POP3 設定檔: {config_file}")
    except Exception as e:
        print(f"⚠️ 無法儲存 POP3 設定檔: {e}")

    return default_config


def _create_default_imap_config(config_file):
    default_config = {
        "known_providers": {
            "gmail.com": [
                {
                    "server": "imap.gmail.com",
                    "port": 993,
                    "ssl": True
                }
            ],
            "outlook.com": [
                {
                    "server": "outlook.office365.com",
                    "port": 993,
                    "ssl": True
                }
            ],
            "yahoo.com": [
                {
                    "server": "imap.mail.yahoo.com",
                    "port": 993,
                    "ssl": True
                }
            ],
            "hotmail.com": [
                {
                    "server": "outlook.office365.com",
                    "port": 993,
                    "ssl": True
                }
            ],
            "cycu.edu.tw": [
                {
                    "server": "imap.cycu.edu.tw",
                    "port": 993,
                    "ssl": True
                },
                {
                    "server": "mail.cycu.edu.tw",
                    "port": 143,
                    "ssl": False
                }
            ],
            "qq.com": [
                {
                    "server": "imap.qq.com",
                    "port": 993,
                    "ssl": True
                }
            ],
            "163.com": [
                {
                    "server": "imap.163.com",
                    "port": 993,
                    "ssl": True
                }
            ],
            "126.com": [
                {
                    "server": "imap.126.com",
                    "port": 993,
                    "ssl": True
                }
            ],
            "aol.com": [
                {
                    "server": "imap.aol.com",
                    "port": 993,
                    "ssl": True
                }
            ],
            "icloud.com": [
                {
                    "server": "imap.mail.me.com",
                    "port": 993,
                    "ssl": True
                }
            ],
            "protonmail.com": [
                {
                    "server": "imap.protonmail.ch",
                    "port": 993,
                    "ssl": True
                }
            ]
        },
        "server_patterns": [
            "imap.{domain}",
            "imap4.{domain}",
            "mail.{domain}",
            "imap.{domain}.com",
            "imap4.{domain}.com",
            "mail.{domain}.com",
            "imap01.{domain}",
            "imap02.{domain}",
            "imap-mail.{domain}",
            "imap4-mail.{domain}"
        ],
        "ports_to_try": [
            993,
            143
        ],
        "timeout_settings": {
            "connection_timeout": 10,
            "read_timeout": 30
        },
        "imap_features": {
            "support_idle": True,
            "support_namespace": True,
            "support_compress": True,
            "support_acl": True,
            "support_move": True,
            "support_multiappend": True
        }
    }
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        print(f"💾 建立預設 IMAP 設定檔: {config_file}")
    except Exception as e:
        print(f"⚠️ 無法儲存 IMAP 設定檔: {e}")

    return default_config




def auto_load_config(config_type: str, config_file: str = None) -> dict:
    """
    通用設定檔載入函數

    Args:
        config_type: 設定類型 ('smtp', 'pop3', 'imap')
        config_file: 設定檔路徑 (可選，預設為 {config_type}_config.json)

    Returns:
        dict: 設定資料
    """
    # 設定預設檔案名稱
    if config_file is None:
        config_file = f'{config_type}_config.json'


    # 對應的預設設定建立函數
    config_creators = {
        'smtp': _create_default_smtp_config,
        'pop3': _create_default_pop3_config,
        'imap': _create_default_imap_config
    }

    if config_type not in config_creators:
        raise ValueError(f"不支援的設定類型: {config_type}")

    create_default_func = config_creators[config_type]

    try:
        if not os.path.exists(config_file):
            print(f"📄 未找到 {config_type.upper()} 設定檔，建立預設設定")
            return create_default_func(config_file)

        # 讀取設定檔
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # 檔案為空
        if not content:
            print(f"📄 {config_type.upper()} 設定檔為空，建立預設設定")
            return create_default_func(config_file)

        data = json.loads(content)

        # 檢查是否為有效 JSON
        if not data or data == "":
            return create_default_func(config_file)

        return data

    except json.JSONDecodeError:
        print(f"❌ {config_type.upper()} 設定檔格式錯誤，使用預設設定")
        return create_default_func(config_file)
    except Exception as e:
        print(f"❌ {config_type.upper()} 錯誤: {e}")
        return {}


# 保持向後兼容的舊函數
def auto_load_smtp(config_file: str = 'smtp_config.json') -> dict:
    """載入 SMTP 設定 (兼容舊程式碼)"""
    return auto_load_config('smtp', config_file)


def auto_load_pop3(config_file: str = 'pop3_config.json') -> dict:
    """載入 POP3 設定 (兼容舊程式碼)"""
    return auto_load_config('pop3', config_file)


def auto_load_imap(config_file: str = 'imap_config.json') -> dict:
    """載入 IMAP 設定 (兼容舊程式碼)"""
    return auto_load_config('imap', config_file)



