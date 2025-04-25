from django.core.management.base import BaseCommand
from core.utils.xml_parser import parse_xml_file, extract_master_data
from core.utils.data_import import DataImporter
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import master data (Account Groups and Accounts) from MSAll.DAT XML file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the MSAll.DAT file')

    def handle(self, *args, **options):
        try:
            self.stdout.write('Starting master data import...')
            
            # Parse XML file
            root = parse_xml_file(options['file_path'])
            self.stdout.write('XML file parsed successfully')

            # Extract data
            data = extract_master_data(root)
            self.stdout.write(f"Found {len(data['account_groups'])} account groups and {len(data['accounts'])} accounts")

            # Import data
            importer = DataImporter()
            importer.import_master_data(data)
            
            self.stdout.write(self.style.SUCCESS('Master data imported successfully'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing master data: {str(e)}'))
            logger.error(f'Error importing master data: {str(e)}', exc_info=True) 