from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection, connections, DEFAULT_DB_ALIAS
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.state import ProjectState
import sys


class Command(BaseCommand):
    help = 'Executes migrations with interactive confirmation for each table'

    def add_arguments(self, parser):
        parser.add_argument('app_label', nargs='?',
                          help='App label of an application to migrate.')
        parser.add_argument('migration_name', nargs='?',
                          help='Migration name to migrate to.')
        parser.add_argument('--database', default=DEFAULT_DB_ALIAS,
                          help='Database to migrate.')
        parser.add_argument('--fake', action='store_true',
                          help='Mark migrations as run without actually running them.')
        parser.add_argument('--fake-initial', action='store_true',
                          help='Mark initial migrations as run without running them.')
        parser.add_argument('--plan', action='store_true',
                          help='Show the migration plan without executing it.')
        
    def handle(self, *args, **options):
        database = options['database']
        app_label = options.get('app_label')
        migration_name = options.get('migration_name')
        fake = options.get('fake', False)
        fake_initial = options.get('fake_initial', False)
        plan = options.get('plan', False)
        
        # If plan option is given, just show the plan and exit
        if plan:
            return self._show_plan(database, app_label, migration_name)
            
        # Get the migration executor
        executor = MigrationExecutor(connections[database])
        
        # Get pending migrations
        plan = executor.migration_plan([(app_label, migration_name)] if app_label else None)
        
        if not plan:
            self.stdout.write(self.style.SUCCESS("No migrations to apply."))
            return
            
        self.stdout.write(self.style.MIGRATE_HEADING("Operations to perform:"))
        
        # Create a list to track confirmed migrations
        confirmed_migrations = []
        
        # Go through the plan and confirm each migration
        for migration, backwards in plan:
            migration_string = f"{migration.app_label}.{migration.name}"
            
            # Get the operations
            operations = migration.operations
            
            self.stdout.write(f"Migration: {migration_string}")
            
            # Ask for each create model operation
            for operation in operations:
                operation_name = operation.__class__.__name__
                
                if operation_name == 'CreateModel':
                    table_name = operation.name
                    confirm = input(f"Create table {table_name} [y/n]? ").lower()
                    
                    if confirm == 'y':
                        confirmed_migrations.append((migration, backwards))
                        self.stdout.write(self.style.SUCCESS(f"  - Will create table: {table_name}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  - Skipping table: {table_name}"))
                else:
                    # For non-CreateModel operations, show what they are
                    op_desc = getattr(operation, 'describe', lambda: operation_name)()
                    self.stdout.write(f"  - {op_desc}")
                    confirmed_migrations.append((migration, backwards))
        
        # If no migrations are confirmed, exit
        if not confirmed_migrations:
            self.stdout.write(self.style.WARNING("No migrations confirmed to apply."))
            return
            
        # Apply confirmed migrations
        self.stdout.write(self.style.MIGRATE_HEADING("Applying confirmed migrations:"))
        
        if fake:
            self.stdout.write(self.style.WARNING("Faking migrations"))
        
        for migration, backwards in confirmed_migrations:
            migration_string = f"{migration.app_label}.{migration.name}"
            self.stdout.write(f"  Applying {migration_string}...", ending="")
            
            try:
                executor.apply_migration(migration, project_state=executor.loader.project_state(), fake=fake or (fake_initial and executor.loader.detect_soft_applied(migration, project_state=executor.loader.project_state())))
                self.stdout.write(self.style.SUCCESS(" OK"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(" ERROR"))
                self.stdout.write(self.style.ERROR(f"    {e}"))
                raise CommandError("Migration failed. See above for details.")
                
        self.stdout.write(self.style.SUCCESS("All confirmed migrations applied successfully."))
        
    def _show_plan(self, database, app_label, migration_name):
        """Show the migration plan without executing."""
        executor = MigrationExecutor(connections[database])
        plan = executor.migration_plan([(app_label, migration_name)] if app_label else None)
        
        if not plan:
            self.stdout.write(self.style.SUCCESS("No migrations to apply."))
            return
            
        self.stdout.write(self.style.MIGRATE_HEADING("Planned operations:"))
        
        for migration, backwards in plan:
            migration_string = f"{migration.app_label}.{migration.name}"
            self.stdout.write(f"Migration: {migration_string}")
            
            for operation in migration.operations:
                operation_name = operation.__class__.__name__
                
                if operation_name == 'CreateModel':
                    self.stdout.write(f"  - Create table: {operation.name}")
                else:
                    op_desc = getattr(operation, 'describe', lambda: operation_name)()
                    self.stdout.write(f"  - {op_desc}")