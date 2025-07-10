# CheckjeBon Import Script

Comprehensive Python script for importing CheckjeBon supermarket data into Supabase with price history tracking.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   export SUPABASE_URL="https://your-project.supabase.co"
   export SUPABASE_KEY="your-supabase-service-key"
   export CHECKJEBON_API_KEY="your-checkjebon-api-key"  # Optional
   ```

3. **Run Import**
   ```bash
   python import_checkjebon.py
   ```

## 🚀 Features

- **Data Fetching**: Downloads product data from CheckjeBon API
- **Price History**: Tracks price changes over time with detailed statistics
- **Data Normalization**: Cleans and normalizes product information
- **Duplicate Detection**: Prevents duplicate products using EAN and name matching
- **Bulk Operations**: Efficient batch processing for large datasets
- **Change Detection**: Identifies significant price movements
- **Data Quality**: Validates and reports data quality issues
- **Comprehensive Logging**: Detailed logging and monitoring
- **Error Handling**: Robust error handling with rollback capability
- **Dry Run Mode**: Test imports without writing to database

## 🎯 Usage Examples

### Basic Import
```bash
python import_checkjebon.py
```

### Test Run (No Database Changes)
```bash
python import_checkjebon.py --dry-run
```

### Import Specific Supermarket
```bash
python import_checkjebon.py --supermarket albert-heijn
```

### Limit Number of Products
```bash
python import_checkjebon.py --limit 1000
```

### Debug Mode
```bash
python import_checkjebon.py --log-level DEBUG
```

### Combined Options
```bash
python import_checkjebon.py --dry-run --supermarket jumbo --limit 500
```

## 🔧 Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SUPABASE_URL` | Your Supabase project URL | Yes | `https://abc123.supabase.co` |
| `SUPABASE_KEY` | Your Supabase service role key | Yes | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `CHECKJEBON_API_KEY` | CheckjeBon API key | No | `your-api-key-here` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

## Data Processing

### Product Categorization
Products are automatically categorized using Dutch keywords:

- **Zuivel & eieren** - melk, yoghurt, kaas, boter, eieren
- **Brood & gebak** - brood, croissant, beschuit, cake
- **Groente & fruit** - appel, banaan, tomaat, sla
- **Vlees, vis & vegetarisch** - vlees, kip, vis, gehakt
- **Dranken** - cola, sap, water, bier, koffie
- **And more...**

### Brand Extraction
Common Dutch brands are automatically detected:
- Albert Heijn, Campina, Douwe Egberts
- Coca Cola, Heineken, Unilever
- Nestlé, Danone, Verkade
- And many more...

### Size Parsing
Dutch size descriptions are parsed into structured data:
- `500ml` → 500, ml
- `1 kg` → 1, kg
- `5 x 250ml` → 1250, ml
- `250 gram` → 250, gram

## Database Schema

The import process works with the following tables:

- `supermarkets` - Dutch supermarket chains
- `categories` - Product categories with Dutch keywords
- `products` - Product information with normalized names
- `product_prices` - Current pricing information
- `price_history` - Historical price tracking

## Logging

All import activities are logged to:
- Console output (with colors)
- `supabase_import.log` file

Log levels:
- `INFO` - General progress information
- `ERROR` - Error conditions
- `DEBUG` - Detailed debugging (with --verbose)

## Error Handling

The import process includes robust error handling:

- **Network errors** - Automatic retry with exponential backoff
- **Database errors** - Graceful failure with detailed error messages
- **Data validation** - Skips invalid records with logging
- **Rate limiting** - Small delays between batches to prevent overwhelming

## Performance

- **Batch processing** - Configurable batch sizes (default: 50)
- **Caching** - Reference data cached for fast lookups
- **Upsert operations** - Efficient handling of duplicates
- **Connection pooling** - Reuses database connections

## Monitoring

The import process provides detailed statistics:

```
📊 IMPORT SUMMARY
============================
Total downloaded entries: 1,234
Products processed: 5,678
Products inserted: 4,500
Products updated: 1,178
Products skipped: 0
Errors encountered: 0
Duration: 45.67s
Processing rate: 124.32 products/second
```

## Daily Automation

For daily automated runs, create a cron job:

```bash
# Run daily at 3 AM
0 3 * * * /path/to/boodschappen_app/supabase_import.py >> /var/log/checkjebon_import.log 2>&1
```

## Troubleshooting

### Common Issues

1. **Environment variables not set**
   ```bash
   export SUPABASE_URL='your_url'
   export SUPABASE_KEY='your_key'
   ```

2. **Database connection failed**
   - Check your Supabase URL and key
   - Verify your project is active
   - Check network connectivity

3. **Permission errors**
   - Ensure your Supabase key has the correct permissions
   - Check Row Level Security policies

4. **Import errors**
   - Check the log file for detailed error messages
   - Use `--dry-run` to test without making changes
   - Use `--verbose` for detailed debugging

### Getting Help

1. Check the log file: `supabase_import.log`
2. Run with `--verbose` for detailed output
3. Test with `--dry-run` to identify issues
4. Verify your database schema matches the expected structure

## Files Overview

- `supabase_import.py` - Main import script
- `setup_supabase_import.sh` - Environment setup script
- `requirements.txt` - Python dependencies
- `IMPORT_README.md` - This documentation
- `database/checkjebon_optimized_schema.sql` - Database schema

## Dependencies

- Python 3.7+
- supabase-py
- requests
- python-dateutil
- postgrest-py
- realtime-py
- storage3