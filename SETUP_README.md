# PostgreSQL Setup for Supreme Octo Succotash

This guide explains how to set up PostgreSQL for the Supreme Octo Succotash application.

## Quick Setup

Run the automated setup script:

```bash
./clean_setup.sh
```

This script will:
- Install PostgreSQL 18 (if not already installed)
- Create the database `supreme_octosuccotash_db`
- Create the user `app_user` with password `app_password`
- Grant necessary permissions
- Initialize all database tables

## Manual Setup (Alternative)

If you prefer to do it step by step:

### 1. Install PostgreSQL
```bash
brew install postgresql@18
brew services start postgresql@18
```

### 2. Create Database and User
```bash
# Create database
psql -h localhost -d postgres -c "CREATE DATABASE supreme_octosuccotash_db;"

# Create user
psql -h localhost -d postgres -c "CREATE USER app_user WITH PASSWORD 'app_password';"

# Grant permissions
psql -h localhost -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE supreme_octosuccotash_db TO app_user;"
```

### 3. Initialize Tables
```bash
python3 init_db.py
```

## Database Configuration

The application connects to PostgreSQL with these settings:
- **Host**: localhost
- **Port**: 5432
- **Database**: supreme_octosuccotash_db
- **User**: app_user
- **Password**: app_password

## Verification

To verify the setup:

```bash
# Test connection
psql -h localhost -d supreme_octosuccotash_db -U app_user -c "SELECT version();"

# Check tables
psql -h localhost -d supreme_octosuccotash_db -U app_user -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
```

## Troubleshooting

### Connection Issues
- Ensure PostgreSQL service is running: `brew services list | grep postgresql`
- Check if the service is started: `brew services start postgresql@18`

### Permission Issues
- Make sure the user has proper permissions on the database
- Verify the password is correct

### Table Creation Issues
- Run `python3 init_db.py` to initialize tables
- Check logs for specific error messages

## Development Notes

- The setup script is idempotent - it can be run multiple times safely
- Database tables are created automatically when repositories are initialized
- The application falls back to SQLite if PostgreSQL is unavailable