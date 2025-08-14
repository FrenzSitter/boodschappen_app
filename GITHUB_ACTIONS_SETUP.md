# GitHub Actions Setup Instructions

## Daily CheckjeBon Import Workflow Setup

This document provides setup instructions for the GitHub Actions workflow that automates daily CheckjeBon imports.

### 1. Repository Secret Configuration

You need to configure the following secret in your GitHub repository:

#### Required Secret:
- **Name:** `IMPORT_SECRET_TOKEN`
- **Value:** `sk_shoplijst_secure_import_token_2025_production_v1`

#### To add the secret:
1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `IMPORT_SECRET_TOKEN`
5. Secret: `sk_shoplijst_secure_import_token_2025_production_v1`
6. Click **Add secret**

### 2. Workflow Configuration

The workflow is configured to:
- **Schedule:** Daily at 10:00 AM Amsterdam time (CET/CEST)
- **Manual Trigger:** Available via GitHub Actions UI
- **Timeout:** 30 minutes maximum execution time

### 3. Workflow Features

#### Timezone Handling
- Automatically handles CET/CEST timezone conversion
- Displays execution time in Amsterdam timezone
- Schedules for 8:00 AM UTC (9:00 AM CET winter, 10:00 AM CEST summer)

#### Health Checks
- Pre-import health validation
- Post-import system verification
- Product count tracking

#### Error Handling
- Comprehensive error logging
- Failure notifications
- Force import option for manual runs

#### Monitoring & Reporting
- Detailed execution summaries
- Success/failure notifications
- Product count tracking
- Performance metrics

### 4. Manual Execution

To manually trigger the import:

1. Go to **Actions** tab in your GitHub repository
2. Select **Daily CheckjeBon Import** workflow
3. Click **Run workflow**
4. Optional: Enable **force_import** to bypass health check failures
5. Click **Run workflow**

### 5. Monitoring

#### Success Indicators:
- ✅ Green workflow status
- Health checks passing
- Import completed successfully
- Product count updated (if applicable)

#### Failure Indicators:
- ❌ Red workflow status
- Failed health checks
- HTTP errors during import
- Timeout errors

#### Logs Location:
- GitHub Actions → Workflows → Daily CheckjeBon Import → Individual run logs

### 6. Production Endpoints

The workflow targets these production endpoints:
- **Base URL:** `https://shoplijst-api-clean-2raak9zlc-epicstories-projects.vercel.app`
- **Health Check:** `/api/health`
- **Import Endpoint:** `/api/import-checkjebon`

### 7. Troubleshooting

#### Common Issues:

1. **Health Check Failures:**
   - Check API availability
   - Verify database connectivity
   - Use force_import for manual runs if needed

2. **Authentication Errors:**
   - Verify `IMPORT_SECRET_TOKEN` secret is correctly set
   - Check token format and permissions

3. **Timezone Issues:**
   - Workflow uses Amsterdam timezone (Europe/Amsterdam)
   - Check execution logs for actual execution time

4. **Import Failures:**
   - Review detailed error logs in workflow output
   - Check API endpoint response codes
   - Verify import endpoint functionality

#### Debugging Steps:
1. Check workflow execution logs
2. Verify API health endpoint manually
3. Test import endpoint with correct authentication
4. Review GitHub Actions secrets configuration

### 8. Notifications

The workflow provides:
- **Success Summary:** Detailed report with statistics
- **Failure Alerts:** Error details and troubleshooting info
- **Execution Logs:** Complete audit trail

### 9. Security Considerations

- Authentication token stored as encrypted GitHub secret
- No sensitive data in workflow logs
- Secure API communication over HTTPS
- User-Agent headers for request identification

### 10. Maintenance

#### Regular Tasks:
- Monitor daily execution success rate
- Review import statistics trends
- Update authentication tokens when needed
- Adjust schedule if timezone requirements change

#### Updates:
- Workflow file: `.github/workflows/daily-import.yml`
- Configuration changes require repository push
- Secret updates via GitHub Settings

---

**Note:** This workflow is designed for production use with comprehensive error handling and monitoring. For development or testing, use the manual trigger option with appropriate force settings.