from django.core.management.base import BaseCommand
from core.models import Account
import os

class Command(BaseCommand):
    help = 'Import account types from master>DAT file'

    def handle(self, *args, **kwargs):
        try:
            # Path to your DAT file
            dat_file_path = 'data/master/account_types.dat'
            
            if not os.path.exists(dat_file_path):
                self.stdout.write(self.style.ERROR(f'File not found: {dat_file_path}'))
                return

            # Read and process the DAT file
            with open(dat_file_path, 'r') as file:
                account_types = []
                for line in file:
                    # Remove whitespace and newlines
                    account_type = line.strip()
                    if account_type:
                        # Convert to the format used in Account model
                        account_type_key = account_type.lower().replace(' ', '_')
                        account_types.append((account_type_key, account_type))

            # Update the Account model's ACCOUNT_TYPES
            existing_types = dict(Account.ACCOUNT_TYPES)
            new_types = dict(account_types)

            # Merge existing and new types
            merged_types = {**existing_types, **new_types}
            
            # Update the model's ACCOUNT_TYPES
            Account.ACCOUNT_TYPES = sorted(merged_types.items())

            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {len(account_types)} account types')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing account types: {str(e)}')
            ) 