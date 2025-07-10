#!/bin/bash

# CheckjeBon Data Analysis Setup Script
# This script installs dependencies and runs the analysis

echo "🔧 CheckjeBon Data Analysis Setup"
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"

# Install required packages
echo "📦 Installing required packages..."
pip3 install requests supabase python-dateutil

echo ""
echo "🏃 Running CheckjeBon data analysis..."
python3 checkjebon_summary.py

echo ""
echo "✅ Analysis complete!"
echo ""
echo "📁 Files created:"
echo "  • analyze_checkjebon_data.py (full analysis script)"
echo "  • checkjebon_summary.py (quick summary script)"
echo "  • requirements.txt (dependencies)"
echo ""
echo "🚀 Next steps:"
echo "  1. Review the analysis above"
echo "  2. Set up your Supabase database using setup_database.sql"
echo "  3. Use the Flutter app's admin panel to import the complete dataset"