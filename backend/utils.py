import struct
from datetime import datetime
from .models import Account, Transaction

def read_masters_dat(file_path):
    """Read and parse masters.DAT file"""
    accounts = []
    with open(file_path, 'rb') as f:
        while True:
            # Read fixed-length fields
            try:
                code = f.read(20).decode('utf-8').strip('\x00')
                name = f.read(100).decode('utf-8').strip('\x00')
                account_type = f.read(20).decode('utf-8').strip('\x00')
                group = f.read(50).decode('utf-8').strip('\x00')
                is_active = struct.unpack('?', f.read(1))[0]
                gst_number = f.read(15).decode('utf-8').strip('\x00')
                pan_number = f.read(10).decode('utf-8').strip('\x00')
                
                if not code:  # End of file
                    break
                    
                accounts.append({
                    'code': code,
                    'name': name,
                    'account_type': account_type,
                    'group': group,
                    'is_active': is_active,
                    'gst_number': gst_number if gst_number else None,
                    'pan_number': pan_number if pan_number else None,
                })
            except struct.error:
                break
    return accounts

def read_transactions_dat(file_path):
    """Read and parse transactions.DAT file"""
    transactions = []
    with open(file_path, 'rb') as f:
        while True:
            try:
                # Read date (8 bytes)
                date_bytes = f.read(8)
                if not date_bytes:
                    break
                date = datetime.strptime(date_bytes.decode('utf-8'), '%Y%m%d').date()
                
                # Read other fields
                description = f.read(200).decode('utf-8').strip('\x00')
                amount = struct.unpack('d', f.read(8))[0]
                type = f.read(10).decode('utf-8').strip('\x00')
                category = f.read(50).decode('utf-8').strip('\x00')
                account_code = f.read(20).decode('utf-8').strip('\x00')
                
                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': amount,
                    'type': type,
                    'category': category,
                    'account_code': account_code,
                })
            except struct.error:
                break
    return transactions

def import_dat_files(masters_path, transactions_path):
    """Import data from both .DAT files into the database"""
    # Import accounts
    accounts = read_masters_dat(masters_path)
    for account_data in accounts:
        Account.objects.update_or_create(
            code=account_data['code'],
            defaults=account_data
        )
    
    # Import transactions
    transactions = read_transactions_dat(transactions_path)
    for trans_data in transactions:
        try:
            account = Account.objects.get(code=trans_data['account_code'])
            Transaction.objects.create(
                date=trans_data['date'],
                description=trans_data['description'],
                amount=trans_data['amount'],
                type=trans_data['type'],
                category=trans_data['category'],
                account=account
            )
        except Account.DoesNotExist:
            print(f"Account not found: {trans_data['account_code']}")
            continue 