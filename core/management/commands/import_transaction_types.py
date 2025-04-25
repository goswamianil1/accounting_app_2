from django.core.management.base import BaseCommand
from core.models import Transaction
import os

class Command(BaseCommand):
    help = 'Import transaction types from Transaction>DAT file'

    def handle(self, *args, **kwargs):
        try:
            # Path to your DAT file
            dat_file_path = 'data/transaction/types.dat'
            
            if not os.path.exists(dat_file_path):
                self.stdout.write(self.style.ERROR(f'File not found: {dat_file_path}'))
                return

            # Read and process the DAT file
            with open(dat_file_path, 'r') as file:
                transaction_types = []
                for line in file:
                    # Remove whitespace and newlines
                    transaction_type = line.strip()
                    if transaction_type:
                        # Convert to the format used in Transaction model
                        type_key = transaction_type.lower().replace(' ', '_')
                        transaction_types.append((type_key, transaction_type))

            # Update the Transaction model's TRANSACTION_TYPES
            existing_types = dict(Transaction.TRANSACTION_TYPES)
            new_types = dict(transaction_types)

            # Merge existing and new types
            merged_types = {**existing_types, **new_types}
            
            # Update the model's TRANSACTION_TYPES
            Transaction.TRANSACTION_TYPES = sorted(merged_types.items())

            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {len(transaction_types)} transaction types')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing transaction types: {str(e)}')
            ) 