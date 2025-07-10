# CheckjeBon Daily Import Installation Guide

This guide provides step-by-step instructions for setting up automated daily imports of CheckjeBon data on different platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Linux Installation](#linux-installation)
3. [macOS Installation](#macos-installation)
4. [Windows Installation](#windows-installation)
5. [Production Deployment](#production-deployment)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting, ensure you have:

- Python 3.7 or higher
- Access to a Supabase project with the CheckjeBon schema
- Your Supabase URL and API key
- Git (for cloning the repository)
- Internet access for downloading data

## Linux Installation

### Ubuntu/Debian

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install Python and required packages
sudo apt install python3 python3-pip python3-venv git cron -y

# 3. Clone or navigate to your project directory
cd /opt
sudo git clone https://github.com/your-repo/boodschappen_app.git
# OR: Copy your project files to /opt/boodschappen_app
sudo chown -R $USER:$USER /opt/boodschappen_app

# 4. Navigate to project directory
cd /opt/boodschappen_app

# 5. Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 7. Configure environment variables
./automation/setup_environment.sh setup

# 8. Test the setup
./automation/setup_environment.sh test

# 9. Set up cron job
./automation/cron_setup.sh install

# 10. Test the automation
./automation/daily_import.sh --dry-run
```

### CentOS/RHEL/Fedora

```bash
# 1. Update system packages
sudo yum update -y  # or dnf update -y for Fedora

# 2. Install Python and required packages
sudo yum install python3 python3-pip git cronie -y  # or dnf install

# 3. Enable and start cron service
sudo systemctl enable crond
sudo systemctl start crond

# 4. Follow steps 3-10 from Ubuntu/Debian section
```

### systemd Service (Production)

```bash
# 1. Create systemd service files
sudo cp automation/checkjebon-import.service /etc/systemd/system/
sudo cp automation/checkjebon-import.timer /etc/systemd/system/

# 2. Edit service file with correct paths
sudo nano /etc/systemd/system/checkjebon-import.service
# Update User, WorkingDirectory, and ExecStart paths

# 3. Create environment file
sudo cp .env /etc/default/checkjebon-import

# 4. Enable and start the timer
sudo systemctl daemon-reload
sudo systemctl enable checkjebon-import.timer
sudo systemctl start checkjebon-import.timer

# 5. Check timer status
sudo systemctl status checkjebon-import.timer
```

## macOS Installation

### Using Homebrew

```bash
# 1. Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python and Git
brew install python3 git

# 3. Navigate to project directory
cd ~/Documents  # or your preferred location
git clone https://github.com/your-repo/boodschappen_app.git
cd boodschappen_app

# 4. Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 5. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 6. Configure environment variables
./automation/setup_environment.sh setup

# 7. Test the setup
./automation/setup_environment.sh test

# 8. Set up cron job
./automation/cron_setup.sh install

# 9. Test the automation
./automation/daily_import.sh --dry-run
```

### Using macOS System Python

```bash
# 1. Install pip (if not available)
sudo easy_install pip

# 2. Install virtualenv
sudo pip install virtualenv

# 3. Follow steps 3-9 from the Homebrew section
```

### macOS Service (launchd)

```bash
# 1. Create launchd plist file
cat > ~/Library/LaunchAgents/com.checkjebon.import.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.checkjebon.import</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/boodschappen_app/automation/daily_import.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/path/to/boodschappen_app/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/boodschappen_app/logs/launchd_error.log</string>
</dict>
</plist>
EOF

# 2. Update the path in the plist file
nano ~/Library/LaunchAgents/com.checkjebon.import.plist

# 3. Load the service
launchctl load ~/Library/LaunchAgents/com.checkjebon.import.plist

# 4. Enable the service
launchctl enable gui/$(id -u)/com.checkjebon.import
```

## Windows Installation

### Using Windows Subsystem for Linux (WSL)

```bash
# 1. Install WSL2 (if not installed)
# Open PowerShell as Administrator and run:
wsl --install

# 2. Install Ubuntu from Microsoft Store
# Launch Ubuntu and follow Linux installation steps

# 3. Access your project
# Place your project in /mnt/c/your-project-path or clone it in WSL
```

### Using Windows Task Scheduler

```powershell
# 1. Install Python from python.org
# Download and install Python 3.7+ from https://python.org/downloads/

# 2. Install Git
# Download and install Git from https://git-scm.com/download/win

# 3. Open Command Prompt as Administrator
# Navigate to your project directory
cd C:\your-project-path\boodschappen_app

# 4. Set up Python virtual environment
python -m venv venv
venv\Scripts\activate.bat

# 5. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 6. Create Windows batch script
# Create automation\daily_import.bat:
```

Create `automation\daily_import.bat`:

```batch
@echo off
cd /d "C:\your-project-path\boodschappen_app"
call venv\Scripts\activate.bat
python supabase_import.py
```

```powershell
# 7. Set up Task Scheduler
# Open Task Scheduler (taskschd.msc)
# Create Basic Task:
# - Name: CheckjeBon Daily Import
# - Trigger: Daily at 3:00 AM
# - Action: Start a program
# - Program: C:\your-project-path\boodschappen_app\automation\daily_import.bat
```

### Using Windows Service (Advanced)

```powershell
# 1. Install Python Windows Service Wrapper
pip install pywin32

# 2. Create service script (service.py)
# 3. Install service using:
python service.py install

# 4. Start service:
python service.py start
```

## Production Deployment

### Docker Deployment

```dockerfile
# Create Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set up cron job
RUN crontab -l | { cat; echo "0 3 * * * /app/automation/daily_import.sh"; } | crontab -

# Start cron daemon
CMD ["cron", "-f"]
```

```bash
# Build and run
docker build -t checkjebon-import .
docker run -d \
  -e SUPABASE_URL=your-url \
  -e SUPABASE_KEY=your-key \
  -v $(pwd)/logs:/app/logs \
  --name checkjebon-import \
  checkjebon-import
```

### Kubernetes Deployment

```yaml
# kubernetes/cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: checkjebon-import
spec:
  schedule: "0 3 * * *"  # Daily at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: checkjebon-import
            image: checkjebon-import:latest
            command: ["/app/automation/daily_import.sh"]
            env:
            - name: SUPABASE_URL
              valueFrom:
                secretKeyRef:
                  name: supabase-credentials
                  key: url
            - name: SUPABASE_KEY
              valueFrom:
                secretKeyRef:
                  name: supabase-credentials
                  key: key
            volumeMounts:
            - name: logs
              mountPath: /app/logs
          volumes:
          - name: logs
            persistentVolumeClaim:
              claimName: checkjebon-logs
          restartPolicy: OnFailure
```

## Verification

After installation, verify the setup:

```bash
# 1. Test environment setup
./automation/setup_environment.sh validate

# 2. Test database connection
./automation/setup_environment.sh test

# 3. Test import process (dry run)
./automation/daily_import.sh --dry-run

# 4. Check cron job
crontab -l | grep checkjebon

# 5. Test email notifications (if enabled)
python automation/email_notifications.py test --to your-email@example.com

# 6. Check logs
ls -la logs/

# 7. Run health check
./automation/daily_import.sh --health
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x automation/*.sh
   sudo chown -R $USER:$USER /path/to/project
   ```

2. **Python Virtual Environment Issues**
   ```bash
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Cron Job Not Running**
   ```bash
   # Check cron service
   sudo systemctl status cron  # or crond
   
   # Check cron logs
   sudo tail -f /var/log/cron  # or /var/log/syslog
   
   # Test cron job manually
   ./automation/daily_import.sh --test
   ```

4. **Database Connection Issues**
   ```bash
   # Verify environment variables
   ./automation/setup_environment.sh show
   
   # Test connection
   ./automation/setup_environment.sh test
   
   # Check network connectivity
   ping your-project.supabase.co
   ```

5. **Email Notifications Not Working**
   ```bash
   # Test email configuration
   python automation/email_notifications.py test --to your-email@example.com
   
   # Check environment variables
   grep EMAIL .env
   ```

### Log Files

- **Main import log**: `logs/daily_import.log`
- **Error log**: `logs/import_errors.log`
- **Success log**: `logs/import_success.log`
- **Cron log**: `logs/cron/daily_import_cron.log`

### Support

For additional help:

1. Check the logs for detailed error messages
2. Use `--verbose` flag for debugging
3. Test with `--dry-run` to identify issues
4. Verify all environment variables are set correctly
5. Check system requirements and dependencies

## Security Considerations

1. **Environment Variables**: Store sensitive data in environment variables, not in code
2. **File Permissions**: Ensure log files and scripts have appropriate permissions
3. **Network Security**: Use HTTPS for all external connections
4. **Regular Updates**: Keep Python dependencies updated
5. **Monitoring**: Set up monitoring for failed imports

## Maintenance

### Regular Tasks

1. **Log Rotation**: Logs are automatically rotated (configurable)
2. **Dependency Updates**: Update Python packages monthly
3. **Health Checks**: Monitor import success rates
4. **Disk Space**: Monitor log directory disk usage
5. **Backup**: Regular backup of configuration and logs

### Automated Maintenance

The system includes automated maintenance tasks:

- Daily imports at 3:00 AM
- Weekly health checks
- Monthly log cleanup
- Quarterly connectivity tests

These can be customized by editing the cron configuration.