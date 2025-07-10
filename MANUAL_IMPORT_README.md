# Manual Database Import Tool

Comprehensive manual fallback system for importing CheckjeBon data when automation fails. This tool provides step-by-step import process with validation, rollback functionality, and detailed reporting.

## 🔧 Features

- **Manual Data Download**: Downloads data from APIs or creates sample data for testing
- **Interactive Mode**: Step-by-step execution with user confirmation
- **Dry-Run Mode**: Test the import process without making actual changes
- **Data Validation**: Comprehensive schema and quality checks
- **Conflict Resolution**: Multiple strategies for handling existing data
- **Rollback Functionality**: Restore previous state if import fails
- **Progress Tracking**: Real-time progress updates and status reporting
- **Detailed Logging**: Comprehensive logs for debugging and audit trails

## 📋 Prerequisites

### Environment Setup

1. **Set Environment Variables**:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-supabase-service-key"
export CHECKJEBON_URL="https://api.checkjebon.nl"  # Optional
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

Required packages:
- `supabase>=1.0.0`
- `requests>=2.28.0`
- `pandas>=2.0.0`
- `aiohttp>=3.8.0`
- `tqdm>=4.65.0` (optional, for progress bars)

## 🚀 Quick Start

### Basic Usage

```bash
# Show current status
python3 manual_import.py --status

# Run full import in interactive mode
python3 manual_import.py --interactive

# Test import without making changes
python3 manual_import.py --dry-run

# Run automated import (non-interactive)
python3 manual_import.py
```

### Step-by-Step Import

```bash
# Download data only
python3 manual_import.py --step download

# Validate downloaded data
python3 manual_import.py --step validate

# Create backup before import
python3 manual_import.py --step backup

# Import specific tables
python3 manual_import.py --step import_supermarkets
python3 manual_import.py --step import_categories
python3 manual_import.py --step import_products
python3 manual_import.py --step import_prices

# Verify import results
python3 manual_import.py --step verify

# Clean up temporary files
python3 manual_import.py --step cleanup
```

## 📝 Command Line Options

```bash
python3 manual_import.py [OPTIONS]

Options:
  -i, --interactive              Run in interactive mode
  -d, --dry-run                 Test run without making changes
  -s, --step STEP               Run a single step
  -c, --conflict-resolution     Strategy for handling conflicts
  -l, --log-level LEVEL         Set logging level (DEBUG, INFO, WARNING, ERROR)
  --status                      Show current import status
  --rollback IMPORT_ID          Rollback using specific backup ID

Conflict Resolution Options:
  skip          Skip existing records
  update        Update existing records
  create_new    Create new records with new IDs
  ask_user      Ask user for each conflict (interactive mode only)

Available Steps:
  download                Download data from APIs
  validate                Validate data structure and quality
  backup                  Create backup of existing data
  import_supermarkets     Import supermarkets data
  import_categories       Import categories data
  import_products         Import products data
  import_prices           Import prices data
  verify                  Verify import results
  cleanup                 Clean up temporary files
```

## 💡 Usage Examples

### Example 1: Interactive Import
```bash
python3 manual_import.py --interactive
```
This will:
1. Show a banner with import information
2. Ask for confirmation before each step
3. Allow you to choose sample data vs. API download
4. Handle conflicts by asking user for each decision
5. Offer rollback if any step fails

### Example 2: Automated Import with Conflict Handling
```bash
python3 manual_import.py --conflict-resolution skip --log-level INFO
```
This will:
1. Run all steps automatically
2. Skip any existing records (no conflicts)
3. Show detailed info-level logging
4. Generate comprehensive reports

### Example 3: Test Run
```bash
python3 manual_import.py --dry-run --interactive
```
This will:
1. Run through all steps without making database changes
2. Show what would be imported
3. Validate all data
4. Generate reports showing what would happen

### Example 4: Selective Import
```bash
# First download and validate
python3 manual_import.py --step download
python3 manual_import.py --step validate

# Then import only specific tables
python3 manual_import.py --step import_supermarkets
python3 manual_import.py --step import_categories

# Verify results
python3 manual_import.py --step verify
```

### Example 5: Recovery from Failed Import
```bash
# Check status of previous import
python3 manual_import.py --status

# Rollback to previous state
python3 manual_import.py --rollback manual_20241209_143022
```

## 📊 Data Sources and Structure

### Expected Table Schemas

#### Supermarkets
```json
{
  "id": "uuid",
  "name": "string",
  "slug": "string", 
  "logo_url": "string",
  "color_primary": "string",
  "website_url": "string",
  "api_endpoint": "string",
  "is_active": "boolean"
}
```

#### Categories
```json
{
  "id": "uuid",
  "name": "string",
  "slug": "string",
  "parent_id": "uuid",
  "description": "string",
  "is_active": "boolean"
}
```

#### Products
```json
{
  "id": "uuid",
  "name": "string",
  "normalized_name": "string",
  "brand": "string",
  "size_text": "string",
  "ean": "string",
  "category_id": "uuid",
  "image_url": "string",
  "is_active": "boolean",
  "description": "string",
  "unit_size": "number",
  "supermarket_id": "uuid"
}
```

#### Prices
```json
{
  "id": "uuid",
  "product_id": "uuid",
  "supermarket_id": "uuid",
  "price": "decimal",
  "price_per_unit": "decimal",
  "original_price": "decimal",
  "is_on_sale": "boolean",
  "discount_percentage": "decimal",
  "price_date": "date",
  "import_batch_id": "string",
  "is_available": "boolean"
}
```

## 📁 File Structure

The tool creates several directories and files:

```
project_root/
├── manual_import_data/           # Downloaded data files
│   ├── supermarkets_[import_id].json
│   ├── categories_[import_id].json
│   ├── products_[import_id].json
│   └── prices_[import_id].json
├── manual_import_backups/        # Database backups
│   └── backup_[import_id].json
├── manual_import_reports/        # Import reports
│   ├── import_report_[import_id].json
│   ├── validation_[import_id].json
│   └── verification_[import_id].json
└── logs/                         # Log files
    └── manual_import_[timestamp].log
```

## 📋 Import Process Flow

### 1. Download Phase
- Attempts to download data from configured APIs
- Falls back to sample data if APIs are unavailable
- Saves raw data to JSON files for processing

### 2. Validation Phase
- Validates JSON structure against expected schemas
- Checks data quality and completeness
- Generates validation reports with compliance metrics

### 3. Backup Phase
- Creates backup of existing database tables
- Stores backup data for potential rollback
- Skipped in dry-run mode

### 4. Import Phase
- Imports data table by table in dependency order:
  1. Supermarkets (no dependencies)
  2. Categories (no dependencies)
  3. Products (depends on categories and supermarkets)
  4. Prices (depends on products and supermarkets)
- Handles conflicts based on configured strategy
- Processes data in configurable batches

### 5. Verification Phase
- Compares imported data counts with source data
- Validates referential integrity
- Generates verification reports

### 6. Cleanup Phase
- Removes temporary files
- Keeps essential reports and backups

## 🔄 Conflict Resolution

When importing data that already exists in the database, the tool can handle conflicts in several ways:

### Skip (Default for Non-Interactive)
```bash
python3 manual_import.py --conflict-resolution skip
```
- Leaves existing records unchanged
- Only imports new records
- Fastest option for incremental updates

### Update
```bash
python3 manual_import.py --conflict-resolution update
```
- Updates existing records with new data
- Preserves record IDs
- Good for data refresh scenarios

### Create New
```bash
python3 manual_import.py --conflict-resolution create_new
```
- Creates new records with new UUIDs
- Preserves both old and new data
- Useful for data migration scenarios

### Ask User (Default for Interactive)
```bash
python3 manual_import.py --interactive
```
- Prompts user for each conflict
- Allows per-record decision making
- Best for careful manual imports

## 📊 Reporting and Monitoring

### Import Reports
Each import generates detailed reports including:
- Step-by-step execution status
- Record counts (processed, inserted, updated, skipped)
- Error messages and warnings
- Execution times and performance metrics

### Validation Reports
Data validation generates reports with:
- Schema compliance percentages
- Field coverage analysis
- Data quality issues
- Recommendations for improvement

### Verification Reports
Post-import verification includes:
- Database vs. source record counts
- Data integrity checks
- Import success confirmation

## 🔧 Troubleshooting

### Common Issues

#### 1. Supabase Connection Failed
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test connection manually
python3 -c "
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('Connection successful')
"
```

#### 2. API Download Failed
```bash
# Use sample data instead
python3 manual_import.py --step download --interactive
# Choose "Yes (use sample data)" when prompted
```

#### 3. Validation Errors
```bash
# Check validation report
cat manual_import_reports/validation_[import_id].json

# Fix data and re-validate
python3 manual_import.py --step validate
```

#### 4. Import Conflicts
```bash
# Use different conflict resolution
python3 manual_import.py --conflict-resolution skip

# Or handle manually in interactive mode
python3 manual_import.py --interactive
```

### Recovery Procedures

#### Rollback Failed Import
```bash
# Check available backups
ls manual_import_backups/

# Rollback to specific backup
python3 manual_import.py --rollback manual_20241209_143022
```

#### Clean Start
```bash
# Remove all import data
rm -rf manual_import_data/
rm -rf manual_import_reports/

# Start fresh import
python3 manual_import.py --interactive
```

## 🔒 Security Considerations

### Environment Variables
- Store sensitive credentials in environment variables
- Never commit credentials to version control
- Use `.env` files for local development

### Data Validation
- All input data is validated before import
- SQL injection protection through parameterized queries
- Schema validation prevents malformed data

### Backup Strategy
- Automatic backups before any data modification
- Rollback capability for failed imports
- Backup retention and cleanup policies

## 📈 Performance Optimization

### Batch Processing
```bash
# Configure batch size via environment
export IMPORT_BATCH_SIZE=500
python3 manual_import.py
```

### Parallel Processing
The tool processes tables in optimal dependency order and uses batch operations for performance.

### Memory Management
- Streams large datasets instead of loading in memory
- Configurable batch sizes for memory control
- Automatic cleanup of temporary files

## 🎯 Best Practices

### Development Environment
```bash
# Always use dry-run first
python3 manual_import.py --dry-run

# Test with sample data
python3 manual_import.py --step download --interactive
# Choose sample data option
```

### Production Environment
```bash
# Create backup first
python3 manual_import.py --step backup

# Use skip conflict resolution for incremental updates
python3 manual_import.py --conflict-resolution skip

# Monitor logs
tail -f logs/manual_import_*.log
```

### Data Quality
1. Always validate data before import
2. Review validation reports for issues
3. Use interactive mode for initial imports
4. Test conflict resolution strategies

### Monitoring
1. Check import reports for errors
2. Verify data counts after import
3. Monitor application logs for issues
4. Set up alerting for failed imports

## 📞 Support

For additional support:
1. Check the troubleshooting section above
2. Review log files in the `logs/` directory
3. Examine detailed reports in `manual_import_reports/`
4. Use `--status` flag to check current state
5. Contact the development team for complex issues

## 🔄 Version History

- **v1.0.0**: Initial release with core import functionality
- **v1.1.0**: Added interactive mode and conflict resolution
- **v1.2.0**: Added rollback functionality and improved reporting
- **v1.3.0**: Added data validation and verification steps

---

**Note**: This tool is designed as a fallback when automated systems fail. For regular operations, use the main automated import system described in the main documentation.