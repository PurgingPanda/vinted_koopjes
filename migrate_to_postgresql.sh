#!/bin/bash

# Migration script from SQLite to PostgreSQL
# Run this after setting up PostgreSQL on your VPS

set -e

echo "🔄 Migrating Vinted Koopjes from SQLite to PostgreSQL..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}📦 Installing PostgreSQL adapter...${NC}"
pip install psycopg2-binary

echo -e "${YELLOW}💾 Backing up current SQLite data...${NC}"
python manage.py dumpdata --natural-foreign --natural-primary \
    --exclude=auth.permission \
    --exclude=contenttypes \
    --exclude=admin.logentry \
    --exclude=sessions.session \
    > backup_data.json

echo -e "${GREEN}✅ Data backed up to backup_data.json${NC}"

echo -e "${YELLOW}🔄 Running PostgreSQL migrations...${NC}"
python manage.py migrate --settings=settings_postgresql

echo -e "${YELLOW}📊 Loading data into PostgreSQL...${NC}"
python manage.py loaddata backup_data.json --settings=settings_postgresql

echo -e "${GREEN}✅ Data migration completed!${NC}"

echo -e "${YELLOW}🧹 Cleaning up...${NC}"
rm backup_data.json

echo -e "${GREEN}🎉 Migration to PostgreSQL completed successfully!${NC}"
echo ""
echo "To use PostgreSQL by default, update your manage.py or set:"
echo "export DJANGO_SETTINGS_MODULE=settings_postgresql"
echo ""
echo "Or update start_all.sh to use the new settings."