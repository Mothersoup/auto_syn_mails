from emailClient import MailClient
from email_processor import EmailProcessor
from mail_reader import MailReaders


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