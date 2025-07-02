# Database Setup Guide

## Supabase Setup

1. **Create a Supabase Project**
   - Go to https://supabase.com
   - Create a new project
   - Note your project URL and anon key

2. **Configure Flutter App**
   - Update `lib/config/supabase_config.dart` with your credentials:
   ```dart
   static const String supabaseUrl = 'YOUR_SUPABASE_URL';
   static const String supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY';
   ```

3. **Run Database Migrations**
   - In your Supabase dashboard, go to SQL Editor
   - Execute the following files in order:
     1. `database/schema.sql` - Creates all tables and relationships
     2. `database/seed_data.sql` - Adds sample Dutch supermarket data

## Data Import

### Import Checkjebon Data

1. **Run the Import Script**
   ```bash
   cd boodschappen_app
   dart run scripts/import_checkjebon_data.dart
   ```

2. **Execute Generated SQL**
   - The script will create SQL files in the `database/` folder
   - Run these files in your Supabase SQL editor to import product data

### Manual Data Entry

You can also manually add products using the Supabase dashboard or through the app interface.

## Database Schema Overview

### Core Tables

- **supermarkets** - Dutch supermarket chains (AH, Jumbo, Lidl, etc.)
- **categories** - Product categories with hierarchical structure
- **products** - Product information (name, brand, barcode, etc.)
- **product_prices** - Current prices per supermarket
- **price_history** - Historical price tracking

### User Data Tables

- **shopping_lists** - User shopping lists
- **shopping_list_items** - Items in shopping lists
- **user_favorites** - User favorite products

## Features

### Price Comparison
- Real-time price comparison across supermarkets
- Price per unit calculations
- Sale and discount tracking

### Data Management
- Automatic price history tracking
- Full-text search on product names
- Category-based filtering

### Performance
- Optimized indexes for fast queries
- Views for common data access patterns
- Efficient price comparison queries

## Security

The database uses Row Level Security (RLS) for user data protection. Public product and price data is accessible to all users, while personal data like shopping lists is protected.