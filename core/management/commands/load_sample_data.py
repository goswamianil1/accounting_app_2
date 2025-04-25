import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import AccountGroup, Account, PurchaseVoucher, ItemEntry, BillSundry, AccountEntry
from datetime import datetime

class Command(BaseCommand):
    help = 'Load sample data from XML files'

    def add_arguments(self, parser):
        parser.add_argument('xml_file', type=str, help='Path to the XML file')

    def handle(self, *args, **options):
        xml_file = options['xml_file']
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            with transaction.atomic():
                # Load account groups
                for group_elem in root.findall('.//AccountGroup'):
                    group = AccountGroup.objects.create(
                        name=group_elem.find('name').text,
                        is_active=group_elem.find('is_active').text.lower() == 'true'
                    )
                    self.stdout.write(f'Created account group: {group.name}')

                # Load accounts
                for account_elem in root.findall('.//Account'):
                    group = AccountGroup.objects.get(name=account_elem.find('group').text)
                    account = Account.objects.create(
                        name=account_elem.find('name').text,
                        code=account_elem.find('code').text,
                        account_type=account_elem.find('account_type').text,
                        group=group,
                        is_active=account_elem.find('is_active').text.lower() == 'true',
                        gst_number=account_elem.find('gst_number').text,
                        pan_number=account_elem.find('pan_number').text
                    )
                    self.stdout.write(f'Created account: {account.name}')

                # Load purchase vouchers
                for voucher_elem in root.findall('.//PurchaseVoucher'):
                    party = Account.objects.get(name=voucher_elem.find('party').text)
                    voucher = PurchaseVoucher.objects.create(
                        voucher_number=voucher_elem.find('voucher_number').text,
                        date=datetime.strptime(voucher_elem.find('date').text, '%Y-%m-%d').date(),
                        voucher_type=voucher_elem.find('voucher_type').text,
                        party=party,
                        total_amount=float(voucher_elem.find('total_amount').text),
                        gst_amount=float(voucher_elem.find('gst_amount').text),
                        net_amount=float(voucher_elem.find('net_amount').text),
                        narration=voucher_elem.find('narration').text
                    )

                    # Load item entries
                    for item_elem in voucher_elem.findall('.//ItemEntry'):
                        ItemEntry.objects.create(
                            purchase_voucher=voucher,
                            item_name=item_elem.find('item_name').text,
                            quantity=float(item_elem.find('quantity').text),
                            rate=float(item_elem.find('rate').text),
                            amount=float(item_elem.find('amount').text),
                            hsn_code=item_elem.find('hsn_code').text,
                            gst_rate=float(item_elem.find('gst_rate').text),
                            gst_amount=float(item_elem.find('gst_amount').text)
                        )

                    # Load bill sundries
                    for sundry_elem in voucher_elem.findall('.//BillSundry'):
                        BillSundry.objects.create(
                            purchase_voucher=voucher,
                            name=sundry_elem.find('name').text,
                            amount=float(sundry_elem.find('amount').text),
                            gst_rate=float(sundry_elem.find('gst_rate').text),
                            gst_amount=float(sundry_elem.find('gst_amount').text)
                        )

                    # Load account entries
                    for entry_elem in voucher_elem.findall('.//AccountEntry'):
                        account = Account.objects.get(name=entry_elem.find('account').text)
                        AccountEntry.objects.create(
                            purchase_voucher=voucher,
                            account=account,
                            entry_type=entry_elem.find('entry_type').text,
                            amount=float(entry_elem.find('amount').text),
                            narration=entry_elem.find('narration').text
                        )

                    self.stdout.write(f'Created purchase voucher: {voucher.voucher_number}')

            self.stdout.write(self.style.SUCCESS('Successfully loaded sample data'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading sample data: {str(e)}')) 