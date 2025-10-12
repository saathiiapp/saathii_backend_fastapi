# Background Tasks Summary

This document provides a comprehensive overview of the Saathii Backend background task system, including all available documentation and resources.

## Documentation Overview

The background task system is documented across multiple files:

### 1. Main Documentation
- **[Background Tasks](./background-tasks.md)** - Complete system overview and setup guide
- **[Background Tasks API](./background-tasks-api.md)** - Programmatic API reference
- **[Background Tasks Setup Guide](../guides/background-tasks-setup.md)** - Detailed setup and maintenance guide

### 2. Related Documentation
- **[Call Management](../api/call-management.md)** - Call-related endpoints and functionality
- **[User Management](../api/user-management.md)** - User presence and status management
- **[Wallet Management](../api/wallets.md)** - Coin and earnings management
- **[WebSocket Real-time](../api/websocket-realtime.md)** - Real-time updates and presence

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Background Task System                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Badge Service │  │ Presence Service│  │ Call Service │ │
│  │                 │  │                 │  │              │ │
│  │ • Daily badges  │  │ • Mark offline  │  │ • Clean calls│ │
│  │ • Performance   │  │ • Clear busy    │  │ • Settle     │ │
│  │ • Earning rates │  │ • Count online  │  │ • Update     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Coin Deduction Service                     │ │
│  │                                                         │ │
│  │ • Per-minute billing                                   │ │
│  │ • Balance checking                                     │ │
│  │ • Call termination                                     │ │
│  │ • Earnings calculation                                 │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Task Schedule

| Task | Frequency | Purpose | Impact |
|------|-----------|---------|---------|
| **Badge Assignment** | Daily (12:01 AM) | Assign listener badges | Affects earning rates |
| **Presence Cleanup** | Every 5 minutes | Mark inactive users offline | Improves feed accuracy |
| **Call Cleanup** | Every 10 minutes | Clean expired calls | Ensures proper billing |
| **Coin Deduction** | Every minute | Deduct coins for calls | Real-time billing |
| **Log Rotation** | Daily (1:00 AM) | Clean old logs | Prevents disk issues |

## Quick Start Guide

### 1. Automated Setup

```bash
# Navigate to project directory
cd /path/to/saathii_backend_fastapi

# Run automated setup
chmod +x background_tasks/scripts/setup_cron.sh
./background_tasks/scripts/setup_cron.sh
```

### 2. Manual Setup

```bash
# Create log directory
sudo mkdir -p /var/log/saathii
sudo chown $(whoami):$(whoami) /var/log/saathii

# Make scripts executable
chmod +x background_tasks/scripts/*.py

# Add cron jobs
crontab -e
# Add the cron entries from the setup guide
```

### 3. Verify Setup

```bash
# Check cron jobs
crontab -l | grep saathii

# Test scripts manually
python3 background_tasks/scripts/badge_assignment.py
python3 background_tasks/scripts/presence_cleanup.py
python3 background_tasks/scripts/call_cleanup.py
python3 background_tasks/scripts/coin_deduction.py
```

## Service Details

### Badge Assignment Service

**Purpose**: Assigns daily badges to listeners based on performance  
**Schedule**: Daily at 12:01 AM  
**Key Functions**:
- Calculates call duration for each listener
- Assigns badges (Basic, Bronze, Silver, Gold)
- Updates earning rates

**Database Impact**:
- Reads: `user_calls` table
- Updates: `user_status` table
- Creates: Badge assignment logs

### Presence Cleanup Service

**Purpose**: Maintains accurate user presence status  
**Schedule**: Every 5 minutes  
**Key Functions**:
- Marks inactive users as offline
- Clears expired busy statuses
- Maintains online user count

**Database Impact**:
- Updates: `user_status` table
- Reads: `user_status` table for counts

### Call Cleanup Service

**Purpose**: Cleans up expired calls and settles billing  
**Schedule**: Every 10 minutes  
**Key Functions**:
- Finds calls with expired wait_time
- Settles listener earnings
- Updates user presence
- Cleans Redis cache

**Database Impact**:
- Reads: `user_calls`, `user_status` tables
- Updates: `user_calls`, `user_wallets` tables
- Creates: Transaction records

### Coin Deduction Service

**Purpose**: Real-time billing for ongoing calls  
**Schedule**: Every minute  
**Key Functions**:
- Deducts coins per minute
- Checks user balance
- Ends calls when coins insufficient
- Updates Redis cache

**Database Impact**:
- Reads: `user_calls`, `user_wallets` tables
- Updates: `user_wallets`, `user_calls` tables
- Creates: Transaction records

## Monitoring and Maintenance

### Log Files

All tasks log to `/var/log/saathii/`:
- `badge_assignment.log` - Badge assignment activities
- `presence_cleanup.log` - Presence cleanup activities
- `call_cleanup.log` - Call cleanup activities
- `coin_deduction.log` - Coin deduction activities

### Monitoring Commands

```bash
# Real-time log monitoring
tail -f /var/log/saathii/badge_assignment.log
tail -f /var/log/saathii/presence_cleanup.log
tail -f /var/log/saathii/call_cleanup.log
tail -f /var/log/saathii/coin_deduction.log

# Check cron jobs
crontab -l | grep saathii

# Check recent activity
grep CRON /var/log/syslog | grep saathii
```

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "🔍 Checking Saathii Background Tasks Health..."

# Check recent log activity
find /var/log/saathii -name "*.log" -mmin -60 -exec echo "✅ {} - Updated within last hour" \;

# Check cron jobs
crontab -l | grep saathii

# Check database connectivity
python3 -c "from api.clients.db import get_db_pool; import asyncio; asyncio.run(get_db_pool())" && echo "✅ Database OK" || echo "❌ Database Error"

# Check Redis connectivity
python3 -c "from api.clients.redis_client import redis_client; import asyncio; asyncio.run(redis_client.ping())" && echo "✅ Redis OK" || echo "❌ Redis Error"
```

## Troubleshooting

### Common Issues

1. **Scripts not executing**
   - Check cron service: `sudo systemctl status cron`
   - Verify script permissions: `ls -la background_tasks/scripts/*.py`
   - Check cron logs: `grep CRON /var/log/syslog`

2. **Database connection errors**
   - Check PostgreSQL status: `sudo systemctl status postgresql`
   - Verify environment variables: `echo $DATABASE_URL`
   - Test connection: `python3 -c "from api.clients.db import get_db_pool; import asyncio; asyncio.run(get_db_pool())"`

3. **Redis connection errors**
   - Check Redis status: `sudo systemctl status redis`
   - Test connection: `redis-cli ping`
   - Verify environment variables: `echo $REDIS_URL`

4. **Permission errors**
   - Check log directory: `ls -la /var/log/saathii/`
   - Fix permissions: `sudo chown -R $(whoami):$(whoami) /var/log/saathii/`
   - Check script permissions: `chmod +x background_tasks/scripts/*.py`

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run scripts with debug output
python3 background_tasks/scripts/badge_assignment.py
```

## Performance Optimization

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_calls_status ON user_calls(status);
CREATE INDEX IF NOT EXISTS idx_user_calls_start_time ON user_calls(start_time);
CREATE INDEX IF NOT EXISTS idx_user_status_last_seen ON user_status(last_seen);
CREATE INDEX IF NOT EXISTS idx_user_status_is_online ON user_status(is_online);
```

### System Optimization

```bash
# Increase file descriptor limits
ulimit -n 65536

# Optimize cron performance
# In /etc/cron.conf:
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
```

## Security Considerations

### File Permissions

```bash
# Set secure permissions
chmod 600 /var/log/saathii/*.log
chmod 755 background_tasks/scripts/*.py
chmod 600 .env
```

### User Permissions

```bash
# Create dedicated user for background tasks
sudo useradd -r -s /bin/false saathii-tasks

# Run tasks as dedicated user
sudo -u saathii-tasks python3 background_tasks/scripts/badge_assignment.py
```

## Integration Examples

### Programmatic Usage

```python
import asyncio
from background_tasks.services.badge_service import assign_daily_badges
from background_tasks.services.presence_service import mark_inactive_users_offline

async def custom_maintenance():
    """Custom maintenance task"""
    # Assign badges
    stats = await assign_daily_badges()
    print(f"Badge assignment: {stats}")
    
    # Clean up presence
    count = await mark_inactive_users_offline(inactive_minutes=5)
    print(f"Marked {count} users offline")

# Run custom maintenance
asyncio.run(custom_maintenance())
```

### Testing Integration

```python
import pytest
from background_tasks.services.badge_service import assign_daily_badges

@pytest.mark.asyncio
async def test_badge_assignment():
    """Test badge assignment functionality"""
    stats = await assign_daily_badges()
    assert stats['total_listeners'] >= 0
    assert stats['errors'] == 0
```

## Backup and Recovery

### Log Backup

```bash
#!/bin/bash
# backup_logs.sh

BACKUP_DIR="/backup/saathii/logs/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
cp -r /var/log/saathii/* "$BACKUP_DIR/"
gzip "$BACKUP_DIR"/*.log
echo "Logs backed up to $BACKUP_DIR"
```

### Configuration Backup

```bash
# Backup crontab
crontab -l > crontab_backup.txt

# Backup environment
cp .env .env.backup
```

## Scaling Considerations

### High Load Scenarios

- Monitor database performance
- Consider read replicas for reporting
- Optimize Redis memory usage
- Scale background task frequency if needed

### Multiple Instances

- Ensure only one instance runs badge assignment
- Use Redis for coordination
- Monitor task overlap
- Implement task locking if needed

### Cloud Deployment

- Use managed databases (RDS, Cloud SQL)
- Use managed Redis (ElastiCache, Memorystore)
- Consider serverless functions for tasks
- Implement proper monitoring and alerting

## Conclusion

The background task system is essential for maintaining the health and accuracy of the Saathii Backend API. It ensures:

- **Accurate user presence** through regular cleanup
- **Proper call billing** through per-minute coin deduction
- **Fair listener compensation** through badge-based earnings
- **System reliability** through automated maintenance

### Key Benefits

1. **Automated Maintenance**: Reduces manual intervention
2. **Real-time Billing**: Ensures accurate call charges
3. **Fair Compensation**: Rewards listeners based on performance
4. **System Health**: Maintains data accuracy and consistency
5. **Scalability**: Handles high user loads efficiently

### Next Steps

1. **Set up** the background task system using the provided guides
2. **Monitor** logs and system performance regularly
3. **Test** individual services before full deployment
4. **Implement** proper error handling and alerting
5. **Scale** the system as your user base grows

For detailed information, refer to the specific documentation files mentioned in this summary.
