# Background Tasks Setup Guide

This guide provides detailed instructions for setting up, monitoring, and maintaining the Saathii Backend background tasks system.

## Prerequisites

Before setting up background tasks, ensure you have:

- **Python 3.8+** installed and accessible via `python3`
- **PostgreSQL** database running and accessible
- **Redis** server running and accessible
- **Cron** service available on your system
- **Proper environment variables** configured
- **Database tables** created and migrated

## Quick Setup

### 1. Automated Setup (Recommended)

The easiest way to set up all background tasks:

```bash
# Navigate to your project directory
cd /path/to/saathii_backend_fastapi

# Make the setup script executable
chmod +x background_tasks/scripts/setup_cron.sh

# Run the automated setup
./background_tasks/scripts/setup_cron.sh
```

This will:
- Create log directory at `/var/log/saathii/`
- Set up all cron jobs with proper paths
- Make all Python scripts executable
- Test script execution
- Display current crontab entries

### 2. Verify Setup

After running the setup script, verify everything is working:

```bash
# Check if cron jobs are installed
crontab -l | grep saathii

# Check log directory
ls -la /var/log/saathii/

# Test script execution manually
python3 background_tasks/scripts/badge_assignment.py
```

## Manual Setup

If you prefer to set up tasks manually or need custom configuration:

### 1. Create Log Directory

```bash
# Create log directory
sudo mkdir -p /var/log/saathii

# Set proper ownership
sudo chown $(whoami):$(whoami) /var/log/saathii

# Set permissions
chmod 755 /var/log/saathii
```

### 2. Make Scripts Executable

```bash
# Navigate to scripts directory
cd background_tasks/scripts/

# Make all Python scripts executable
chmod +x *.py

# Verify permissions
ls -la *.py
```

### 3. Configure Cron Jobs

Edit your crontab:

```bash
crontab -e
```

Add these entries (adjust paths as needed):

```cron
# Saathii Backend Essential Scheduled Tasks

# Badge assignment - runs daily at 12:01 AM
1 0 * * * cd /path/to/saathii_backend_fastapi && python3 background_tasks/scripts/badge_assignment.py >> /var/log/saathii/badge_assignment.log 2>&1

# Presence cleanup - runs every 5 minutes
*/5 * * * * cd /path/to/saathii_backend_fastapi && python3 background_tasks/scripts/presence_cleanup.py >> /var/log/saathii/presence_cleanup.log 2>&1

# Call cleanup - runs every 10 minutes
*/10 * * * * cd /path/to/saathii_backend_fastapi && python3 background_tasks/scripts/call_cleanup.py >> /var/log/saathii/call_cleanup.log 2>&1

# Coin deduction - runs every minute
* * * * * cd /path/to/saathii_backend_fastapi && python3 background_tasks/scripts/coin_deduction.py >> /var/log/saathii/coin_deduction.log 2>&1

# Log rotation - runs daily at 1:00 AM
0 1 * * * find /var/log/saathii -name "*.log" -mtime +7 -delete
```

### 4. Test Individual Scripts

Test each script manually to ensure they work:

```bash
# Test badge assignment
python3 background_tasks/scripts/badge_assignment.py

# Test presence cleanup
python3 background_tasks/scripts/presence_cleanup.py

# Test call cleanup
python3 background_tasks/scripts/call_cleanup.py

# Test coin deduction
python3 background_tasks/scripts/coin_deduction.py
```

## Environment Configuration

### Required Environment Variables

Ensure these environment variables are set:

```bash
# Database configuration
DATABASE_URL=postgresql://username:password@localhost:5432/saathii_db

# Redis configuration
REDIS_URL=redis://localhost:6379/0

# Logging level
LOG_LEVEL=INFO

# S3 configuration (for file uploads)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your_bucket_name
AWS_REGION=your_region
```

### Environment File

Create a `.env` file in your project root:

```bash
# .env
DATABASE_URL=postgresql://username:password@localhost:5432/saathii_db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your_bucket_name
AWS_REGION=us-east-1
```

## Monitoring and Maintenance

### 1. Log Monitoring

Monitor background task logs:

```bash
# Real-time monitoring
tail -f /var/log/saathii/badge_assignment.log
tail -f /var/log/saathii/presence_cleanup.log
tail -f /var/log/saathii/call_cleanup.log
tail -f /var/log/saathii/coin_deduction.log

# View recent activity
tail -n 100 /var/log/saathii/badge_assignment.log

# Search for errors
grep -i error /var/log/saathii/*.log

# Search for specific patterns
grep "insufficient coins" /var/log/saathii/coin_deduction.log
```

### 2. System Monitoring

Monitor system resources and cron activity:

```bash
# Check cron job status
crontab -l | grep saathii

# Check recent cron activity
grep CRON /var/log/syslog | grep saathii

# Monitor system resources
htop
iostat 1

# Check disk space
df -h /var/log/saathii/
```

### 3. Health Check Script

Create a health check script:

```bash
#!/bin/bash
# health_check.sh

echo "🔍 Checking Saathii Background Tasks Health..."
echo "=============================================="

# Check if logs are being updated
echo "📊 Recent log activity:"
find /var/log/saathii -name "*.log" -mmin -60 -exec echo "✅ {} - Updated within last hour" \;

# Check cron jobs
echo ""
echo "⏰ Active cron jobs:"
crontab -l | grep saathii

# Check database connectivity
echo ""
echo "🗄️ Database connectivity:"
python3 -c "
import asyncio
import sys
sys.path.append('.')
from api.clients.db import get_db_pool

async def test_db():
    try:
        pool = await get_db_pool()
        print('✅ Database connection successful')
        await pool.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test_db())
"

# Check Redis connectivity
echo ""
echo "🔴 Redis connectivity:"
python3 -c "
import asyncio
import sys
sys.path.append('.')
from api.clients.redis_client import redis_client

async def test_redis():
    try:
        await redis_client.ping()
        print('✅ Redis connection successful')
    except Exception as e:
        print(f'❌ Redis connection failed: {e}')

asyncio.run(test_redis())
"

echo ""
echo "✅ Health check completed!"
```

Make it executable and run:

```bash
chmod +x health_check.sh
./health_check.sh
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Scripts Not Executing

**Symptoms**: Cron jobs are set up but scripts don't run

**Solutions**:
```bash
# Check if scripts are executable
ls -la background_tasks/scripts/*.py

# Check cron service status
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog

# Test script execution manually
python3 background_tasks/scripts/badge_assignment.py
```

#### 2. Database Connection Errors

**Symptoms**: Scripts fail with database connection errors

**Solutions**:
```bash
# Check database status
sudo systemctl status postgresql

# Test database connection
python3 -c "
import asyncio
from api.clients.db import get_db_pool
asyncio.run(get_db_pool())
"

# Check environment variables
echo $DATABASE_URL
```

#### 3. Redis Connection Errors

**Symptoms**: Scripts fail with Redis connection errors

**Solutions**:
```bash
# Check Redis status
sudo systemctl status redis

# Test Redis connection
python3 -c "
import asyncio
from api.clients.redis_client import redis_client
asyncio.run(redis_client.ping())
"

# Check Redis configuration
redis-cli ping
```

#### 4. Permission Errors

**Symptoms**: Scripts fail with permission denied errors

**Solutions**:
```bash
# Check log directory permissions
ls -la /var/log/saathii/

# Fix permissions
sudo chown -R $(whoami):$(whoami) /var/log/saathii/
chmod 755 /var/log/saathii/

# Check script permissions
chmod +x background_tasks/scripts/*.py
```

#### 5. Path Issues

**Symptoms**: Scripts can't find modules or files

**Solutions**:
```bash
# Check current working directory in cron
# Add absolute paths to cron jobs

# Test from correct directory
cd /path/to/saathii_backend_fastapi
python3 background_tasks/scripts/badge_assignment.py
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set debug log level
export LOG_LEVEL=DEBUG

# Run script with debug output
python3 background_tasks/scripts/badge_assignment.py
```

### Log Analysis

Analyze logs for patterns and issues:

```bash
# Count errors by type
grep -i error /var/log/saathii/*.log | cut -d: -f2 | sort | uniq -c

# Find most common errors
grep -i error /var/log/saathii/*.log | head -20

# Check performance metrics
grep "completed successfully" /var/log/saathii/*.log | tail -10
```

## Performance Optimization

### 1. Database Optimization

Optimize database performance for background tasks:

```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_calls_status ON user_calls(status);
CREATE INDEX IF NOT EXISTS idx_user_calls_start_time ON user_calls(start_time);
CREATE INDEX IF NOT EXISTS idx_user_status_last_seen ON user_status(last_seen);
CREATE INDEX IF NOT EXISTS idx_user_status_is_online ON user_status(is_online);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM user_calls WHERE status = 'ongoing';
```

### 2. Redis Optimization

Optimize Redis for background tasks:

```bash
# Configure Redis for better performance
# In redis.conf:
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. System Optimization

Optimize system resources:

```bash
# Increase file descriptor limits
ulimit -n 65536

# Optimize cron performance
# In /etc/cron.conf:
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
```

## Security Considerations

### 1. File Permissions

Secure log files and scripts:

```bash
# Set secure permissions
chmod 600 /var/log/saathii/*.log
chmod 755 background_tasks/scripts/*.py

# Restrict access to sensitive files
chmod 600 .env
```

### 2. User Permissions

Run background tasks with appropriate user:

```bash
# Create dedicated user for background tasks
sudo useradd -r -s /bin/false saathii-tasks

# Run tasks as dedicated user
sudo -u saathii-tasks python3 background_tasks/scripts/badge_assignment.py
```

### 3. Network Security

Secure database and Redis connections:

```bash
# Use SSL for database connections
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Use Redis AUTH
REDIS_URL=redis://:password@localhost:6379/0
```

## Backup and Recovery

### 1. Log Backup

Backup important logs:

```bash
# Create log backup script
#!/bin/bash
# backup_logs.sh

BACKUP_DIR="/backup/saathii/logs/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Copy logs
cp -r /var/log/saathii/* "$BACKUP_DIR/"

# Compress old logs
gzip "$BACKUP_DIR"/*.log

echo "Logs backed up to $BACKUP_DIR"
```

### 2. Configuration Backup

Backup cron configuration:

```bash
# Backup crontab
crontab -l > crontab_backup.txt

# Backup environment
cp .env .env.backup
```

### 3. Recovery Procedures

Recovery from common failures:

```bash
# Restore crontab
crontab crontab_backup.txt

# Restore environment
cp .env.backup .env

# Restart services
sudo systemctl restart cron
sudo systemctl restart postgresql
sudo systemctl restart redis
```

## Scaling Considerations

### 1. High Load Scenarios

For high user loads:

- Monitor database performance
- Consider read replicas for reporting
- Optimize Redis memory usage
- Scale background task frequency if needed

### 2. Multiple Instances

For multiple API instances:

- Ensure only one instance runs badge assignment
- Use Redis for coordination
- Monitor task overlap
- Implement task locking if needed

### 3. Cloud Deployment

For cloud deployments:

- Use managed databases (RDS, Cloud SQL)
- Use managed Redis (ElastiCache, Memorystore)
- Consider serverless functions for tasks
- Implement proper monitoring and alerting

## Conclusion

The background tasks system is essential for the proper functioning of the Saathii Backend API. Proper setup, monitoring, and maintenance ensure:

- **Accurate user presence** through regular cleanup
- **Proper call billing** through per-minute coin deduction
- **Fair listener compensation** through badge-based earnings
- **System reliability** through automated maintenance

Follow this guide to set up and maintain a robust background task system that keeps your Saathii application running smoothly.
