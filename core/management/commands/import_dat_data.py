from django.core.management.base import BaseCommand
import os
from core.models import Account, Transaction
from datetime import datetime

class Command(BaseCommand):
    help = 'Import data from DAT files'

    def handle(self, *args, **kwargs):
        # Path to DAT files
        transaction_file = 'Transaction.DAT'
        masters_file = 'Masters.DAT'

        # Import Masters data
        if os.path.exists(masters_file):
            try:
                with open(masters_file, 'r', encoding='utf-8') as file:
                    self._import_masters(file)
            except UnicodeDecodeError:
                with open(masters_file, 'r', encoding='latin-1') as file:
                    self._import_masters(file)

        # Import Transaction data
        if os.path.exists(transaction_file):
            try:
                with open(transaction_file, 'r', encoding='utf-8') as file:
                    self._import_transactions(file)
            except UnicodeDecodeError:
                with open(transaction_file, 'r', encoding='latin-1') as file:
                    self._import_transactions(file)

        self.stdout.write(self.style.SUCCESS('Successfully imported DAT files'))

    def _import_masters(self, file):
        for line in file:
            try:
                data = line.strip().split('|')
                if len(data) >= 2:
                    Account.objects.get_or_create(
                        name=data[0],
                        account_type=data[1].lower() if len(data) > 1 else 'asset'
                    )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing master: {str(e)}'))

    def _import_transactions(self, file):
        for line in file:
            try:
                data = line.strip().split('|')
                if len(data) >= 4:
                    date = datetime.strptime(data[0], '%Y-%m-%d').date()
                    Transaction.objects.get_or_create(
                        date=date,
                        description=data[1],
                        amount=float(data[2]),
                        type=data[3].lower()
                    )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing transaction: {str(e)}')) 