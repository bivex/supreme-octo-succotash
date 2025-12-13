#!/usr/bin/env python3
"""
Database backup script for PostgreSQL.
Creates compressed backups of the supreme_octosuccotash_db database.
"""

import os
import subprocess
import datetime
import gzip
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'supreme_octosuccotash_db',
    'user': 'app_user',
    'password': 'app_password'
}

# Backup directory
BACKUP_DIR = Path('database_backups')
BACKUP_DIR.mkdir(exist_ok=True)

class DatabaseBackup:
    """Handles PostgreSQL database backups."""

    def __init__(self, config: dict):
        self.config = config
        self.backup_dir = BACKUP_DIR

    def create_backup_filename(self) -> str:
        """Generate a timestamped backup filename."""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"supreme_octosuccotash_db_backup_{timestamp}.sql"

    def create_backup(self, compress: bool = True) -> str:
        """
        Create a database backup.

        Args:
            compress: Whether to compress the backup file

        Returns:
            Path to the backup file
        """
        backup_filename = self.create_backup_filename()
        backup_path = self.backup_dir / backup_filename

        logger.info(f"Starting database backup: {backup_path}")

        # Set environment variable for password
        env = os.environ.copy()
        env['PGPASSWORD'] = self.config['password']

        # pg_dump command
        cmd = [
            'pg_dump',
            '-h', self.config['host'],
            '-p', str(self.config['port']),
            '-U', self.config['user'],
            '-d', self.config['database'],
            '-f', str(backup_path),
            '--no-password',  # Use PGPASSWORD environment variable
            '--format=custom',  # Custom format for better compression
            '--compress=9',  # Maximum compression
            '--verbose'
        ]

        try:
            # Run pg_dump
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"Backup created successfully: {backup_path}")
            logger.info(f"Backup size: {backup_path.stat().st_size / (1024*1024):.2f} MB")

            # Optionally compress further with gzip
            if compress:
                compressed_path = backup_path.with_suffix('.sql.gz')
                logger.info(f"Compressing backup to: {compressed_path}")

                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb', compresslevel=9) as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Remove uncompressed file
                backup_path.unlink()
                backup_path = compressed_path

                logger.info(f"Compressed backup size: {backup_path.stat().st_size / (1024*1024):.2f} MB")

            return str(backup_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"Backup failed: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during backup: {e}")
            raise

    def list_backups(self) -> list:
        """List all backup files."""
        backups = []
        for file_path in self.backup_dir.glob('*.sql*'):
            stat = file_path.stat()
            backups.append({
                'filename': file_path.name,
                'path': str(file_path),
                'size_mb': stat.st_size / (1024 * 1024),
                'created': datetime.datetime.fromtimestamp(stat.st_ctime)
            })

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups

    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """
        Remove backups older than specified days.

        Args:
            keep_days: Number of days to keep backups

        Returns:
            Number of files removed
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
        removed_count = 0

        for file_path in self.backup_dir.glob('*.sql*'):
            if datetime.datetime.fromtimestamp(file_path.stat().st_ctime) < cutoff_date:
                file_path.unlink()
                logger.info(f"Removed old backup: {file_path.name}")
                removed_count += 1

        return removed_count

def main():
    """Main function to run the backup."""
    import argparse

    parser = argparse.ArgumentParser(description='PostgreSQL Database Backup Script')
    parser.add_argument('--no-compress', action='store_true', help='Skip gzip compression')
    parser.add_argument('--list', action='store_true', help='List existing backups')
    parser.add_argument('--cleanup', type=int, metavar='DAYS', help='Remove backups older than DAYS (default: 30)')

    args = parser.parse_args()

    backup_manager = DatabaseBackup(DB_CONFIG)

    if args.list:
        backups = backup_manager.list_backups()
        if not backups:
            print("No backups found.")
        else:
            print("Existing backups:")
            print("-" * 80)
            for backup in backups:
                print(f"File: {backup['filename']}")
                print(f"Size: {backup['size_mb']:.2f} MB")
                print(f"Created: {backup['created']}")
                print("-" * 80)
        return

    if args.cleanup is not None:
        removed = backup_manager.cleanup_old_backups(args.cleanup)
        print(f"Removed {removed} old backup files.")
        return

    # Create backup
    compress = not args.no_compress
    backup_path = backup_manager.create_backup(compress=compress)
    print(f"Backup completed: {backup_path}")

if __name__ == '__main__':
    main()