from datetime import datetime, timedelta

from emailClient import MailClient
from email_processor import EmailProcessor
from mail_reader import MailReaders


def main():
    jason_reader_instance = MailReaders()
    clients_dict = jason_reader_instance.load_accounts()
    clients = [MailClient(account_info) for account_info in clients_dict]
    operators_for_clients = [EmailProcessor(client) for client in clients]
    # store multiple mail to check mail
    time_range: dict = {}
    while True:
        try:
            print("\n📅 請選擇時間範圍:")
            print("1. 小時前 (例如: 輸入 2 表示 2小時前)")
            print("2. 天前 (例如: 輸入 3 表示 3天前)")
            print("3. 週前 (例如: 輸入 1 表示 1週前)")
            print("4. 使用預設 (24小時前)")
            print("0. 退出程式")

            choice = input("請選擇 [0-3] (直接Enter使用預設): ").strip()

            if choice == "0" or choice == "":
                print("👋 再見！")
                return
            elif choice == "1":  # 小時
                hours = int(input("請輸入小時數: "))
                time_range = {
                    'start': datetime.now() - timedelta(hours=hours),
                    'end': datetime.now()
                }
                print(f"⏰ 時間範圍: {hours}小時前到現在")
                break
            elif choice == "2":  # 天
                days = int(input("請輸入天數: "))
                time_range = {
                    'start': datetime.now() - timedelta(days=days),
                    'end': datetime.now()
                }
                print(f"⏰ 時間範圍: {days}天前到現在")
                break
            elif choice == "3":  # 週
                weeks = int(input("請輸入週數: "))
                time_range = {
                    'start': datetime.now() - timedelta(weeks=weeks),
                    'end': datetime.now()
                }
                print(f"⏰ 時間範圍: {weeks}週前到現在")
                break
            elif choice == "4":  # 預設
                print("⏰ 使用預設時間範圍: 24小時前")
                break
            else:
                print("❌ 請輸入 0-4 的數字！")

        except ValueError:
            print("❌ 請輸入有效的數字！")
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")

    unique_mail = []
    email_accounts = []
    seen_clean_subjects = set()

    for operator in operators_for_clients:
        print(f"\n=== 帳號: {operator.mail_client.account['email']} ===")
        print(f"可用協定: {operator.mail_client.get_available_protocols()}")
        print(f"收信協定: {operator.mail_client.get_receive_protocol()}")
        emails = operator.get_emails_generic(protocol=operator.mail_client.get_receive_protocol(),
                                             range_date=time_range)
        email_accounts.append(operator.mail_client.account['email'])
        for e in emails:
            # 🎯 先清理主旨
            original_subject = e['subject']
            clean_subject = operator.clean_email_subject(original_subject)
            # 🎯 使用清理後的主旨來比較是否重複
            if clean_subject not in seen_clean_subjects:
                seen_clean_subjects.add(clean_subject)
                unique_mail.append(e)
                print(f"   📧 {clean_subject[:30]}... (新增)")
            else:
                print(f"   📧 {clean_subject[:30]}... (重複，跳過)")
            # 如果是已轉發郵件，特別標記
            print(f"\n🎯 搜尋完成！找到 {len(unique_mail)} 封唯一郵件")

    # 🎯 轉發邏輯
    forwarded_count = 0
    skipped_count = 0

    for operator in operators_for_clients:

        # 取得郵件
        emails = operator.get_emails_generic(
            protocol=operator.mail_client.get_receive_protocol(),
            range_date=time_range
        )

        for e in unique_mail:
            # 🎯 顯示清理前後的主旨對比
            original_subject = e['subject']
            clean_subject = operator.clean_email_subject(original_subject)
            print(f"🔄 檢查郵件: '{original_subject[:40]}...'")
            print(f"   🧹 清理後: '{clean_subject[:40]}...'")

            # 🎯 檢查清理後的主旨，決定是否轉發

            if clean_subject not in list(map(operator.clean_email_subject, map(lambda x: x['subject'], emails))):
                # 🎯 使用新的過濾轉發方法
                success = operator.forward_email(e, [email_account for email_account in email_accounts
                                                     if email_account != operator.mail_client.account['email']])

                if success:
                    forwarded_count += 1
                    print(f"   ✅ 已轉發", clean_subject)
                else:
                    skipped_count += 1
                    print(f"   ❌ 轉發失敗")
            else:
                skipped_count += 1
                print(f"   ⏭️  跳過轉發 (主旨過濾)")

        print("end of account-----------")

    # 🎯 顯示統計資訊
    print(f"\n📊 轉發統計:")
    print(f"   ✅ 成功轉發: {forwarded_count} 封")
    print(f"   ⏭️  跳過轉發: {skipped_count} 封")
    print(f"   📧 總處理: {forwarded_count + skipped_count} 封")


if __name__ == "__main__":
    main()
