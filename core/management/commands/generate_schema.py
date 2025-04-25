from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = 'Generate PostgreSQL schema and seed data'

    def handle(self, *args, **options):
        try:
            # Generate schema
            self.stdout.write('Generating schema...')
            
            # Get all models
            models = apps.get_models()
            
            # Create schema file
            schema_file = 'schema.sql'
            with open(schema_file, 'w') as f:
                # Write header
                f.write('-- PostgreSQL schema for Accounting Management System\n\n')
                
                # Write table creation statements
                for model in models:
                    if model._meta.db_table:
                        f.write(f'-- Table: {model._meta.db_table}\n')
                        f.write(f'CREATE TABLE IF NOT EXISTS {model._meta.db_table} (\n')
                        
                        # Write columns
                        columns = []
                        for field in model._meta.fields:
                            column_def = f'    {field.column} {self._get_postgres_type(field)}'
                            if not field.null:
                                column_def += ' NOT NULL'
                            if field.primary_key:
                                column_def += ' PRIMARY KEY'
                            columns.append(column_def)
                        
                        f.write(',\n'.join(columns))
                        f.write('\n);\n\n')
                
                # Write indexes
                for model in models:
                    if model._meta.db_table:
                        for index in model._meta.indexes:
                            f.write(f'CREATE INDEX IF NOT EXISTS {index.name} ON {model._meta.db_table} ({", ".join(index.fields)});\n')
                        f.write('\n')
                
                # Write foreign keys
                for model in models:
                    if model._meta.db_table:
                        for field in model._meta.fields:
                            if field.remote_field:
                                f.write(f'ALTER TABLE {model._meta.db_table} ADD CONSTRAINT fk_{field.name} FOREIGN KEY ({field.column}) REFERENCES {field.remote_field.model._meta.db_table} ({field.remote_field.model._meta.pk.column});\n')
                        f.write('\n')

            self.stdout.write(self.style.SUCCESS(f'Schema generated successfully: {schema_file}'))

            # Generate seed data
            self.stdout.write('Generating seed data...')
            call_command('load_sample_data', 'sample_data.xml')
            
            self.stdout.write(self.style.SUCCESS('Seed data generated successfully'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating schema: {str(e)}'))

    def _get_postgres_type(self, field):
        """Convert Django field type to PostgreSQL type"""
        if field.get_internal_type() == 'AutoField':
            return 'SERIAL'
        elif field.get_internal_type() == 'BigAutoField':
            return 'BIGSERIAL'
        elif field.get_internal_type() == 'CharField':
            return f'VARCHAR({field.max_length})'
        elif field.get_internal_type() == 'TextField':
            return 'TEXT'
        elif field.get_internal_type() == 'IntegerField':
            return 'INTEGER'
        elif field.get_internal_type() == 'BigIntegerField':
            return 'BIGINT'
        elif field.get_internal_type() == 'DecimalField':
            return f'DECIMAL({field.max_digits}, {field.decimal_places})'
        elif field.get_internal_type() == 'FloatField':
            return 'DOUBLE PRECISION'
        elif field.get_internal_type() == 'BooleanField':
            return 'BOOLEAN'
        elif field.get_internal_type() == 'DateTimeField':
            return 'TIMESTAMP'
        elif field.get_internal_type() == 'DateField':
            return 'DATE'
        elif field.get_internal_type() == 'TimeField':
            return 'TIME'
        elif field.get_internal_type() == 'JSONField':
            return 'JSONB'
        else:
            return 'TEXT'  # Default type 