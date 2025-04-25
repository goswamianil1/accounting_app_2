from django.core.management.base import BaseCommand
from core.utils.xml_parser import parse_xml_file, extract_purchase_data
from core.utils.data_import import DataImporter
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import purchase vouchers from Vh01042023.DAT XML file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Vh01042023.DAT file')

    def handle(self, *args, **options):
        try:
            self.stdout.write('Starting purchase voucher import...')
            
            # Parse XML file
            root = parse_xml_file(options['file_path'])
            self.stdout.write('XML file parsed successfully')

            # Extract data
            vouchers = extract_purchase_data(root)
            self.stdout.write(f"Found {len(vouchers)} purchase vouchers")

            # Import data
            importer = DataImporter()
            importer.import_purchase_vouchers(vouchers)
            
            self.stdout.write(self.style.SUCCESS('Purchase vouchers imported successfully'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing purchase vouchers: {str(e)}'))
            logger.error(f'Error importing purchase vouchers: {str(e)}', exc_info=True) 