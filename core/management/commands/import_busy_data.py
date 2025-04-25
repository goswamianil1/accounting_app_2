import os
import struct
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import AccountGroup, Account, PurchaseVoucher, ItemEntry, BillSundry, AccountEntry
from datetime import datetime

class BusyDATReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file = None
        self.header = None

    def __enter__(self):
        self.file = open(self.file_path, 'rb')
        self._read_header()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()

    def _read_header(self):
        # Read header (first 32 bytes)
        header_data = self.file.read(32)
        self.header = struct.unpack('32s', header_data)[0].decode('utf-8').strip('\x00')

    def read_record(self):
        # Read record length (4 bytes)
        length_data = self.file.read(4)
        if not length_data:
            return None
        
        record_length = struct.unpack('I', length_data)[0]
        
        # Read record data
        record_data = self.file.read(record_length)
        if not record_data:
            return None
        
        # Parse record based on file type
        if 'VH' in self.header:
            return self._parse_voucher_record(record_data)
        elif 'MS' in self.header:
            return self._parse_master_record(record_data)
        return None

    def _parse_voucher_record(self, data):
        # Parse voucher record
        # This is a simplified version - adjust based on actual .DAT file structure
        try:
            voucher_number = data[0:20].decode('utf-8').strip()
            date_str = data[20:28].decode('utf-8')
            date = datetime.strptime(date_str, '%Y%m%d').date()
            amount = struct.unpack('d', data[28:36])[0]
            
            return {
                'type': 'voucher',
                'voucher_number': voucher_number,
                'date': date,
                'amount': amount
            }
        except Exception as e:
            print(f"Error parsing voucher record: {str(e)}")
            return None

    def _parse_master_record(self, data):
        # Parse master record
        # This is a simplified version - adjust based on actual .DAT file structure
        try:
            code = data[0:10].decode('utf-8').strip()
            name = data[10:60].decode('utf-8').strip()
            
            return {
                'type': 'master',
                'code': code,
                'name': name
            }
        except Exception as e:
            print(f"Error parsing master record: {str(e)}")
            return None

class Command(BaseCommand):
    help = 'Import data from Busy .DAT files'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the .DAT file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        try:
            with BusyDATReader(file_path) as reader:
                with transaction.atomic():
                    while True:
                        record = reader.read_record()
                        if not record:
                            break

                        if record['type'] == 'master':
                            self._process_master_record(record)
                        elif record['type'] == 'voucher':
                            self._process_voucher_record(record)

            self.stdout.write(self.style.SUCCESS('Successfully imported data'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing data: {str(e)}'))

    def _process_master_record(self, record):
        # Process master record (accounts, groups, etc.)
        try:
            # Check if account exists
            account, created = Account.objects.get_or_create(
                code=record['code'],
                defaults={
                    'name': record['name'],
                    'account_type': 'ASSET',  # Default type
                    'group': AccountGroup.objects.get_or_create(name='Default')[0],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'Created account: {account.name}')
            else:
                self.stdout.write(f'Account already exists: {account.name}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing master record: {str(e)}'))

    def _process_voucher_record(self, record):
        # Process voucher record
        try:
            # Create or update voucher
            voucher, created = PurchaseVoucher.objects.get_or_create(
                voucher_number=record['voucher_number'],
                defaults={
                    'date': record['date'],
                    'voucher_type': 'PURCHASE',
                    'party': Account.objects.get_or_create(
                        name='Default Party',
                        defaults={
                            'code': '9999',
                            'account_type': 'EXPENSE',
                            'group': AccountGroup.objects.get_or_create(name='Expenses')[0],
                            'is_active': True
                        }
                    )[0],
                    'total_amount': record['amount'],
                    'gst_amount': 0,
                    'net_amount': record['amount']
                }
            )
            
            if created:
                self.stdout.write(f'Created voucher: {voucher.voucher_number}')
            else:
                self.stdout.write(f'Voucher already exists: {voucher.voucher_number}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing voucher record: {str(e)}')) 