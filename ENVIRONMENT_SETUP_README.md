# Environment Setup Verification Guide

Comprehensive verification system for the supermarket data import system environment. This guide covers all aspects of environment setup, validation, and troubleshooting.

## 🎯 Overview

The environment verification script (`verify_environment.py`) performs comprehensive checks to ensure your system is properly configured for the supermarket data import system. It validates everything from environment variables to database connectivity, performance, and security.

## 📋 Verification Categories

### 1. **Environment Variables**
- ✅ **Required Variables**: `SUPABASE_URL`, `SUPABASE_KEY`
- ⚠️ **Optional Variables**: `AWS_*`, `GITHUB_TOKEN`, `REDIS_URL`
- 🔍 **Format Validation**: URL formats, key lengths, syntax checking
- 📄 **File Checks**: `.env` file existence and configuration

### 2. **Dependencies & Connectivity**
- 📦 **Python Packages**: `supabase`, `requests`, `pandas`, `boto3`, etc.
- 🌐 **Network Connectivity**: Internet, DNS, API endpoints
- 📜 **Requirements File**: `requirements.txt` validation
- 🔗 **External APIs**: CheckjeBon, GitHub, AWS services

### 3. **Database Setup**
- 🗄️ **Supabase Connection**: Authentication and connectivity
- 📊 **Table Structure**: Schema validation for all required tables
- 🔐 **Permissions**: CRUD operation testing
- ⚡ **Performance**: Query speed benchmarking

### 4. **External Services**
- 🐙 **GitHub API**: Token validation and repository access
- ☁️ **AWS S3**: Credentials and bucket accessibility
- 🔄 **CI/CD Pipeline**: GitHub Actions configuration
- 📡 **API Endpoints**: External service availability

### 5. **File System**
- 📁 **Directory Structure**: Required directories and permissions
- 💾 **Disk Space**: Available storage verification
- ✍️ **Write Permissions**: Log and data directory access
- 🗂️ **Backup Storage**: Backup directory setup

### 6. **Performance Benchmarks**
- 🖥️ **CPU Performance**: Processing speed testing
- 🧠 **Memory Usage**: Available RAM and usage patterns
- 🗄️ **Database Queries**: Response time benchmarking
- 📊 **System Resources**: Overall performance assessment

### 7. **Security Validation**
- 🔒 **File Permissions**: `.env` file security
- 🔐 **SSL Certificates**: HTTPS endpoint validation
- 🛡️ **Credential Security**: Example value detection
- 🔍 **Security Configuration**: Best practices compliance

## 🚀 Quick Start

### Basic Usage

```bash
# Run all verification checks
python3 verify_environment.py

# Quick check (skip performance benchmarks)
python3 verify_environment.py --quick

# Verbose output with detailed logging
python3 verify_environment.py --verbose

# Save detailed report to file
python3 verify_environment.py --output environment_report.json
```

### Output Formats

```bash
# Summary format (default)
python3 verify_environment.py

# Detailed format with all check details
python3 verify_environment.py --format detailed

# JSON format for automated processing
python3 verify_environment.py --format json
```

## 📝 Command Line Options

```bash
python3 verify_environment.py [OPTIONS]

Options:
  -h, --help                    Show help message
  -v, --verbose                 Enable verbose output with detailed logging
  -q, --quick                   Skip time-consuming checks (performance benchmarks)
  -o, --output FILE             Save detailed report to JSON file
  --format {summary,detailed,json}  Choose output format

Examples:
  python3 verify_environment.py                              # Run all checks
  python3 verify_environment.py --quick                      # Skip performance benchmarks  
  python3 verify_environment.py --verbose                    # Detailed output
  python3 verify_environment.py --output report.json         # Save detailed report
  python3 verify_environment.py --format json | jq           # JSON output with jq
```

## 🔧 Environment Setup

### Required Environment Variables

Create a `.env` file in your project root:

```bash
# Copy example file
cp .env.example .env

# Edit with your actual values
nano .env
```

#### Minimum Required Configuration
```bash
# Supabase Database (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-key

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
```

#### Optional Configuration
```bash
# Test Environment
SUPABASE_TEST_URL=https://your-test-project.supabase.co
SUPABASE_TEST_KEY=your-test-supabase-key

# External APIs
CHECKJEBON_URL=https://api.checkjebon.nl
CHECKJEBON_API_KEY=your-checkjebon-api-key

# AWS Configuration (for backups)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET=your-backup-bucket

# GitHub Configuration (for CI/CD)
GITHUB_TOKEN=your-github-token
GITHUB_REPOSITORY=your-username/your-repo

# Cache and Performance
REDIS_URL=redis://localhost:6379
IMPORT_BATCH_SIZE=1000
REQUEST_TIMEOUT=30

# Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your-email@domain.com
EMAIL_PASSWORD=your-app-password
```

### Dependencies Installation

```bash
# Install all required packages
pip install -r requirements.txt

# Or install individual packages
pip install supabase requests pandas aiohttp psutil

# Optional packages for enhanced functionality
pip install boto3 psycopg2-binary PyGithub
```

## 📊 Understanding Check Results

### Status Indicators

- ✅ **PASS**: Check completed successfully
- ❌ **FAIL**: Critical issue that must be fixed
- ⚠️ **WARN**: Non-critical issue or missing optional feature
- ℹ️ **INFO**: Informational message or optional configuration
- ⏭️ **SKIP**: Check was skipped (e.g., in quick mode)

### Overall Status Ratings

- 🌟 **EXCELLENT**: All checks passed, no warnings
- 👍 **GOOD**: All critical checks passed, minor warnings
- 🔧 **FAIR**: Some minor failures or several warnings
- ❌ **POOR**: Multiple critical failures requiring attention

### Performance Benchmarks

The script includes performance benchmarks for:
- **CPU**: Hash computation speed test
- **Memory**: Available RAM and usage monitoring
- **Database**: Query response time measurement
- **Network**: Connection latency to external services

Benchmark results help identify performance bottlenecks before they impact production.

## 🔍 Troubleshooting Common Issues

### 1. Environment Variable Issues

#### Missing SUPABASE_URL or SUPABASE_KEY
```bash
❌ Environment Variable: SUPABASE_URL: Required variable SUPABASE_URL is not set

Solution:
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-supabase-service-key"
```

#### Invalid URL Format
```bash
⚠️ Environment Variable: SUPABASE_URL: SUPABASE_URL format may be incorrect

Solution: Ensure SUPABASE_URL follows format: https://your-project.supabase.co
```

### 2. Dependency Issues

#### Missing Python Packages
```bash
❌ Python Package: supabase: Critical package supabase is not installed

Solution: Install supabase: pip install supabase
```

#### Requirements File Missing
```bash
⚠️ Requirements File: requirements.txt not found

Solution: Create requirements.txt to document dependencies
```

### 3. Database Connection Issues

#### Connection Failed
```bash
❌ Supabase Connection: Failed to connect to Supabase: Invalid API key

Solution: Verify SUPABASE_KEY is correct and has proper permissions
```

#### Table Missing
```bash
❌ Database Table: supermarkets: Table supermarkets does not exist

Solution: Create table supermarkets by running database migrations:
./scripts/run-migrations.sh
```

### 4. Network Connectivity Issues

#### DNS Resolution Failed
```bash
❌ Network: Google DNS: DNS resolution failed

Solution: Check network connectivity and firewall settings
```

#### API Timeout
```bash
⚠️ Network: CheckjeBon API: Connection timeout to CheckjeBon API

Solution: Check URL configuration and network connectivity
```

### 5. File System Issues

#### Permission Denied
```bash
❌ Directory: logs: Directory exists but no write permission

Solution: Fix permissions: chmod 755 logs
```

#### Insufficient Disk Space
```bash
❌ Disk Space: Critical: Only 0.5 GB free space remaining

Solution: Free up disk space before proceeding
```

### 6. Security Issues

#### Insecure File Permissions
```bash
⚠️ Security: .env File Permissions: .env file permissions are 644 (should be 600)

Solution: Fix permissions: chmod 600 .env
```

#### Example Values Detected
```bash
⚠️ Security: .env Configuration: .env file may contain example values: ['your_', 'example_']

Solution: Replace example values with actual credentials
```

## 🛠️ Manual Verification Steps

Some checks require manual verification that can't be automated:

### 1. Supabase Dashboard Access
1. Log into your Supabase dashboard
2. Verify project is active and accessible
3. Check table structure in the Table Editor
4. Review API usage and quotas

### 2. GitHub Repository Setup
1. Verify repository exists and is accessible
2. Check GitHub Actions are enabled
3. Review secrets configuration in repository settings
4. Ensure proper branch protection rules

### 3. AWS Console Verification
1. Log into AWS console
2. Verify S3 bucket exists and is accessible
3. Check IAM user permissions
4. Review AWS billing for usage

### 4. Network Security
1. Test API endpoints in browser
2. Verify SSL certificates are valid
3. Check firewall rules allow required connections
4. Test from production environment

## 📈 Performance Optimization

### Improving Check Performance

```bash
# Skip performance benchmarks for faster checking
python3 verify_environment.py --quick

# Run specific checks only (modify script as needed)
# Focus on critical checks first
```

### Database Performance

If database queries are slow:
1. Check network latency to Supabase
2. Review query complexity and indexing
3. Consider database plan upgrade if needed
4. Monitor Supabase dashboard for performance metrics

### System Performance

For slow CPU or memory issues:
1. Close unnecessary applications
2. Consider system upgrade if needed
3. Optimize import batch sizes
4. Monitor system resources during operations

## 🔄 Automated Integration

### CI/CD Integration

Add environment verification to your CI/CD pipeline:

```yaml
# .github/workflows/verify-environment.yml
name: Environment Verification

on:
  push:
    branches: [ main, develop ]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Verify Environment
        run: python3 verify_environment.py --quick --format json
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
```

### Monitoring Integration

Use the verification script for ongoing monitoring:

```bash
# Cron job for daily environment checks
0 6 * * * /path/to/verify_environment.py --quick --output /var/log/env-check.json

# Alert on failures
python3 verify_environment.py --quick || echo "Environment check failed" | mail -s "Alert" admin@company.com
```

## 📋 Pre-Deployment Checklist

Before deploying to production, ensure all these checks pass:

### Critical Requirements (Must Pass)
- [ ] ✅ All required environment variables set
- [ ] ✅ Supabase connection successful
- [ ] ✅ All database tables exist with correct schema
- [ ] ✅ Database permissions working (SELECT, COUNT)
- [ ] ✅ Basic network connectivity working
- [ ] ✅ Required directories exist with write permissions
- [ ] ✅ Sufficient disk space available (>5GB)

### Recommended Requirements (Should Pass)
- [ ] ✅ All Python dependencies installed
- [ ] ✅ External APIs accessible (CheckjeBon, GitHub)
- [ ] ✅ AWS S3 configured for backups
- [ ] ✅ Performance benchmarks acceptable
- [ ] ✅ Security configuration proper
- [ ] ✅ SSL certificates valid

### Optional Requirements (Nice to Have)
- [ ] ✅ Test environment configured
- [ ] ✅ Redis caching available
- [ ] ✅ Email notifications configured
- [ ] ✅ Monitoring and alerting setup

## 📊 Report Analysis

### Understanding JSON Output

When using `--format json`, the output includes:

```json
{
  "timestamp": "2024-12-09T15:30:00",
  "system_info": {
    "platform": "macOS-14.0-arm64",
    "python_version": "3.11.6",
    "cpu_count": 8,
    "memory_total": 17179869184
  },
  "overall_status": "GOOD",
  "success_rate": 92.5,
  "summary": {
    "total_checks": 40,
    "passed": 37,
    "failed": 0,
    "warnings": 3,
    "info": 0,
    "skipped": 0
  },
  "performance": {
    "average_benchmark_time": 0.125,
    "benchmark_count": 5
  },
  "results": [...]
}
```

### Key Metrics to Monitor

1. **Success Rate**: Should be >90% for production
2. **Failed Checks**: Should be 0 for deployment
3. **Warning Count**: Monitor and address over time
4. **Benchmark Times**: Track performance trends
5. **System Resources**: Monitor for capacity planning

## 🆘 Getting Help

### Support Resources

1. **Documentation**: Review all README files in the project
2. **Logs**: Check detailed logs in `logs/` directory
3. **Reports**: Analyze JSON reports for detailed information
4. **Troubleshooting**: Use the troubleshooting guide (`TROUBLESHOOTING.md`)

### Contact Information

- **Development Team**: engineer@yourcompany.com
- **DevOps Support**: devops@yourcompany.com
- **Emergency**: emergency@yourcompany.com

### Escalation Process

1. **Level 1**: Use automated verification and self-service fixes
2. **Level 2**: Contact development team with verification report
3. **Level 3**: Escalate to DevOps for infrastructure issues
4. **Emergency**: Contact emergency support for production issues

---

**Remember**: Run environment verification before every deployment and regularly in production to ensure system health and catch issues early.