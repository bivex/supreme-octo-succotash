#!/bin/bash

# Clean PostgreSQL Setup Script for Supreme Octo Succotash
# This script sets up PostgreSQL 18, creates the database and user, and initializes tables

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_NAME="supreme_octosuccotash_db"
DB_USER="app_user"
DB_PASSWORD="app_password"

echo -e "${BLUE}🚀 Starting PostgreSQL setup for Supreme Octo Succotash${NC}"
echo -e "${BLUE}=================================================${NC}"

# Function to print status messages
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Step 1: Install PostgreSQL 18
echo -e "\n${BLUE}Step 1: Installing PostgreSQL 18${NC}"
if command -v psql >/dev/null 2>&1; then
    CURRENT_VERSION=$(psql --version | grep -o '[0-9][0-9]*\.[0-9][0-9]*' | head -1)
    if [[ "$CURRENT_VERSION" == 18.* ]]; then
        print_warning "PostgreSQL 18 is already installed"
    else
        print_warning "Found PostgreSQL $CURRENT_VERSION, upgrading to 18"
        brew services stop postgresql@$CURRENT_VERSION 2>/dev/null || true
        brew install postgresql@18
        brew services start postgresql@18
    fi
else
    print_info "Installing PostgreSQL 18"
    brew install postgresql@18
    brew services start postgresql@18
fi
print_status "PostgreSQL 18 is ready"

# Step 2: Create database and user
echo -e "\n${BLUE}Step 2: Setting up database and user${NC}"

# Check if database exists
DB_EXISTS=$(psql -h localhost -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "")

if [ "$DB_EXISTS" = "1" ]; then
    print_warning "Database '$DB_NAME' already exists"
else
    print_info "Creating database '$DB_NAME'"
    psql -h localhost -d postgres -c "CREATE DATABASE $DB_NAME;"
    print_status "Database '$DB_NAME' created"
fi

# Check if user exists
USER_EXISTS=$(psql -h localhost -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" 2>/dev/null || echo "")

if [ "$USER_EXISTS" = "1" ]; then
    print_warning "User '$DB_USER' already exists"
else
    print_info "Creating user '$DB_USER'"
    psql -h localhost -d postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    print_status "User '$DB_USER' created"
fi

# Grant privileges
print_info "Granting privileges to '$DB_USER' on '$DB_NAME'"
psql -h localhost -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
print_status "Privileges granted"

# Step 3: Test connection
echo -e "\n${BLUE}Step 3: Testing database connection${NC}"
if psql -h localhost -d "$DB_NAME" -U "$DB_USER" -c "SELECT version();" >/dev/null 2>&1; then
    print_status "Database connection test successful"
else
    print_error "Database connection test failed"
    exit 1
fi

# Step 4: Initialize database tables
echo -e "\n${BLUE}Step 4: Initializing database tables${NC}"
print_info "Running database initialization script"
if python3 init_db.py; then
    print_status "Database tables initialized successfully"
else
    print_error "Database initialization failed"
    exit 1
fi

# Step 5: Final verification
echo -e "\n${BLUE}Step 5: Final verification${NC}"

# Check if we can connect and see some tables
TABLE_COUNT=$(psql -h localhost -d "$DB_NAME" -U "$DB_USER" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -gt "0" ]; then
    print_status "Found $TABLE_COUNT database tables"
else
    print_warning "No tables found - initialization may have failed"
fi

echo -e "\n${GREEN}🎉 PostgreSQL setup completed successfully!${NC}"
echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}Database: $DB_NAME${NC}"
echo -e "${GREEN}User: $DB_USER${NC}"
echo -e "${GREEN}Host: localhost:5432${NC}"
echo -e "${YELLOW}Note: Password is stored in this script for automation${NC}"
echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}Your application should now work with PostgreSQL!${NC}"