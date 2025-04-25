from typing import Dict, List, Any
from django.db import transaction
from django.utils.dateparse import parse_date
import logging

from core.models import AccountGroup, Account, PurchaseVoucher, ItemEntry, BillSundry, AccountEntry

logger = logging.getLogger(__name__)

class DataImporter:
    def __init__(self):
        self.group_mapping = {}  # Maps temporary codes to AccountGroup instances
        self.account_mapping = {}  # Maps temporary codes to Account instances

    @transaction.atomic
    def import_master_data(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Import account groups and accounts from parsed XML data."""
        try:
            # First pass: Create all account groups without parent relationships
            for group_data in data['account_groups']:
                group = AccountGroup.objects.create(
                    name=group_data['name'],
                    is_active=group_data['is_active']
                )
                self.group_mapping[group_data['tmp_code']] = group

            # Second pass: Update parent relationships
            for group_data in data['account_groups']:
                if group_data['parent_name']:
                    parent_group = AccountGroup.objects.filter(name=group_data['parent_name']).first()
                    if parent_group:
                        group = self.group_mapping[group_data['tmp_code']]
                        group.parent = parent_group
                        group.save()

            # Import accounts
            for account_data in data['accounts']:
                group = AccountGroup.objects.filter(name=account_data['group_name']).first()
                if not group:
                    logger.warning(f"Group not found for account {account_data['name']}")
                    continue

                # Determine account type based on group hierarchy
                account_type = self._determine_account_type(group)
                
                account = Account.objects.create(
                    name=account_data['name'],
                    code=account_data['code'],
                    account_type=account_type,
                    group=group,
                    gst_number=account_data['gst_number'],
                    pan_number=account_data['pan_number'],
                    address=account_data['address'],
                    is_active=True
                )
                self.account_mapping[account_data['tmp_code']] = account

        except Exception as e:
            logger.error(f"Error importing master data: {str(e)}")
            raise

    def _determine_account_type(self, group: AccountGroup) -> str:
        """Determine account type based on group hierarchy."""
        current = group
        while current:
            name = current.name.upper()
            if 'ASSET' in name:
                return 'ASSET'
            elif 'LIABILITY' in name:
                return 'LIABILITY'
            elif 'INCOME' in name or 'REVENUE' in name:
                return 'INCOME'
            elif 'EXPENSE' in name:
                return 'EXPENSE'
            elif 'CAPITAL' in name or 'EQUITY' in name:
                return 'EQUITY'
            current = current.parent
        return 'ASSET'  # Default type

    @transaction.atomic
    def import_purchase_vouchers(self, vouchers_data: List[Dict[str, Any]]) -> None:
        """Import purchase vouchers with their related entries."""
        try:
            for voucher_data in vouchers_data:
                # Find the party account
                party = Account.objects.filter(name=voucher_data['party_name']).first()
                if not party:
                    logger.warning(f"Party not found: {voucher_data['party_name']}")
                    continue

                # Create the purchase voucher
                voucher = PurchaseVoucher.objects.create(
                    voucher_number=voucher_data['voucher_number'],
                    date=parse_date(voucher_data['date']),
                    voucher_type=voucher_data['voucher_type'],
                    party=party,
                    total_amount=voucher_data['total_amount'],
                    net_amount=voucher_data['net_amount'],
                    narration=voucher_data['narration']
                )

                # Create item entries
                for item_data in voucher_data['items']:
                    ItemEntry.objects.create(
                        purchase_voucher=voucher,
                        item_name=item_data['item_name'],
                        quantity=item_data['quantity'],
                        rate=item_data['rate'],
                        amount=item_data['amount'],
                        hsn_code=item_data['hsn_code'],
                        gst_rate=item_data['gst_rate'],
                        gst_amount=item_data['gst_amount']
                    )

                # Create bill sundries
                for sundry_data in voucher_data['bill_sundries']:
                    BillSundry.objects.create(
                        purchase_voucher=voucher,
                        name=sundry_data['name'],
                        amount=sundry_data['amount'],
                        gst_rate=sundry_data['gst_rate'],
                        gst_amount=sundry_data['gst_amount']
                    )

                # Create account entries
                for entry_data in voucher_data['account_entries']:
                    account = Account.objects.filter(name=entry_data['account_name']).first()
                    if not account:
                        logger.warning(f"Account not found: {entry_data['account_name']}")
                        continue

                    AccountEntry.objects.create(
                        purchase_voucher=voucher,
                        account=account,
                        entry_type=entry_data['entry_type'],
                        amount=entry_data['amount'],
                        narration=entry_data['narration']
                    )

        except Exception as e:
            logger.error(f"Error importing purchase vouchers: {str(e)}")
            raise 