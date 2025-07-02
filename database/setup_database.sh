#!/bin/bash

# Setup database for Boodschappen App
# This script creates tables and seeds data for the Dutch grocery price comparison app

set -e

echo "Setting up Boodschappen App database..."

# You need to run these SQL commands in your Supabase SQL editor
# or use the Supabase CLI if you have it installed

echo "Step 1: Create tables"
echo "Go to your Supabase dashboard > SQL Editor"
echo "Run the contents of: database/create_tables.sql"
echo ""

echo "Step 2: Insert seed data"
echo "Run the contents of: database/seed_data_new.sql"
echo ""

echo "If you have supabase CLI installed, you can run:"
echo "supabase db reset"
echo "Then run the SQL files in your Supabase dashboard"
echo ""

echo "Manual setup instructions:"
echo "1. Go to https://supabase.com/dashboard"
echo "2. Select your project: boodschappen-app"
echo "3. Go to SQL Editor"
echo "4. Copy and paste create_tables.sql contents and run"
echo "5. Copy and paste seed_data_new.sql contents and run"
echo ""

echo "Database setup files ready!"
echo "- Tables: database/create_tables.sql"
echo "- Seed data: database/seed_data_new.sql"