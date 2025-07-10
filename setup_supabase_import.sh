#!/bin/bash

# Supabase Import Setup Script
# ============================
# Setup script for CheckjeBon to Supabase import process

echo "🔧 Supabase Import Setup"
echo "========================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📦 Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "🔐 Environment Variables Setup"
echo "=============================="
echo "You need to set the following environment variables:"
echo ""
echo "export SUPABASE_URL='your_supabase_project_url'"
echo "export SUPABASE_KEY='your_supabase_anon_key'"
echo ""
echo "You can find these in your Supabase project settings:"
echo "1. Go to https://supabase.com/dashboard"
echo "2. Select your project"
echo "3. Go to Settings > API"
echo "4. Copy the URL and anon/public key"
echo ""

# Check if environment variables are set
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "⚠️  Environment variables not set. Please set them before running the import."
    echo ""
    echo "Example:"
    echo "export SUPABASE_URL='https://your-project.supabase.co'"
    echo "export SUPABASE_KEY='your-anon-key-here'"
    echo ""
else
    echo "✅ Environment variables are set"
    echo ""
fi

echo "🚀 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set your Supabase environment variables (see above)"
echo "2. Make sure your database schema is set up (run the SQL file)"
echo "3. Run the import: python supabase_import.py"
echo ""
echo "📖 Usage examples:"
echo "• Test run: python supabase_import.py --dry-run"
echo "• Verbose output: python supabase_import.py --verbose"
echo "• Custom batch size: python supabase_import.py --batch-size=100"
echo "• Help: python supabase_import.py --help"