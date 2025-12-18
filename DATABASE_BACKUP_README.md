# Database Backup Script

This Python script provides automated backup functionality for the PostgreSQL database used in the Supreme Octo
Succotash project.

## Features

- **Compressed Backups**: Uses PostgreSQL's custom format with maximum compression
- **Automatic Compression**: Further compresses with gzip for smaller file sizes
- **Timestamped Files**: Each backup includes creation timestamp
- **Backup Listing**: View all existing backups with sizes and dates
- **Cleanup**: Remove old backups automatically
- **Logging**: Detailed logging of backup operations

## Usage

### Basic Backup

```bash
python3 backup_database.py
```

### Create Uncompressed Backup

```bash
python3 backup_database.py --no-compress
```

### List Existing Backups

```bash
python3 backup_database.py --list
```

### Cleanup Old Backups (Keep Last 30 Days)

```bash
python3 backup_database.py --cleanup 30
```

## Configuration

The script uses the same database configuration as the main application:

- **Host**: localhost
- **Port**: 5432
- **Database**: supreme_octosuccotash_db
- **User**: app_user
- **Password**: app_password

## Backup Location

All backups are stored in the `database_backups/` directory with filenames like:
`supreme_octosuccotash_db_backup_YYYYMMDD_HHMMSS.sql.gz`

## Automation

You can add this to cron for automated backups:

```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/project && python3 backup_database.py

# Weekly cleanup (keep 30 days)
0 3 * * 0 cd /path/to/project && python3 backup_database.py --cleanup 30
```

## Requirements

- Python 3.6+
- PostgreSQL client tools (`pg_dump`)
- Access to the database with configured credentials

## Recovery

To restore from a backup:

```bash
# For compressed backup
gunzip supreme_octosuccotash_db_backup_YYYYMMDD_HHMMSS.sql.gz

# Restore the database
pg_restore -h localhost -p 5432 -U app_user -d supreme_octosuccotash_db supreme_octosuccotash_db_backup_YYYYMMDD_HHMMSS.sql
```

**⚠️ Warning**: Restoring will overwrite existing data. Make sure to backup current data if needed.