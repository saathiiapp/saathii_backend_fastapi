# Background Tasks

The Saathii Backend API includes several critical background tasks that run automatically to maintain system health, process payments, and manage user presence. These tasks are essential for the proper functioning of the application.

## Overview

The background task system consists of:

- **4 Core Services**: Badge assignment, presence cleanup, call cleanup, and coin deduction
- **4 Executable Scripts**: Python scripts that run the services
- **1 Setup Script**: Automated cron job configuration
- **Automated Scheduling**: Cron-based task execution

## Task Schedule

| Task | Frequency | Time | Purpose |
|------|-----------|------|---------|
| Badge Assignment | Daily | 12:01 AM | Assign listener badges based on performance |
| Presence Cleanup | Every 5 minutes | - | Mark inactive users offline |
| Call Cleanup | Every 10 minutes | - | Clean up expired calls |
| Coin Deduction | Every minute | - | Deduct coins for ongoing calls |
| Log Rotation | Daily | 1:00 AM | Clean up old log files |

## Services

### 1. Badge Assignment Service

**File**: `background_tasks/services/badge_service.py`  
**Script**: `background_tasks/scripts/badge_assignment.py`  
**Schedule**: Daily at 12:01 AM

#### Purpose
Assigns daily badges to listeners based on their previous day's call performance. Badges determine earning rates and user status.

#### Functionality
- Calculates total call duration for each listener from the previous day
- Assigns badges based on performance thresholds:
  - **Basic**: 0-59 minutes
  - **Bronze**: 60-119 minutes  
  - **Silver**: 120-179 minutes
  - **Gold**: 180+ minutes
- Updates listener badge status in the database
- Provides detailed statistics and error reporting

#### Key Functions
```python
async def assign_daily_badges():
    """Assign badges for today based on yesterday's performance"""
    # Calculates call duration for each listener
    # Assigns appropriate badge level
    # Returns statistics about assignments
```

#### Database Operations
- **Reads**: `user_calls` table to calculate call durations
- **Updates**: `user_status` table to set new badge levels
- **Creates**: Badge assignment logs

#### Error Handling
- Continues processing even if individual listener assignments fail
- Logs detailed error information
- Returns comprehensive statistics including error counts

---

### 2. Presence Cleanup Service

**File**: `background_tasks/services/presence_service.py`  
**Script**: `background_tasks/scripts/presence_cleanup.py`  
**Schedule**: Every 5 minutes

#### Purpose
Maintains accurate user presence status by marking inactive users as offline and cleaning up expired busy statuses.

#### Functionality
- **Inactive User Detection**: Marks users as offline if they haven't been seen for 5+ minutes
- **Busy Status Cleanup**: Clears expired busy statuses (when wait_time ≤ 0)
- **Presence Accuracy**: Ensures the online user count is accurate
- **Performance Monitoring**: Tracks how many users are marked offline

#### Key Functions
```python
async def mark_inactive_users_offline(inactive_minutes: int = 5):
    """Mark users as offline if inactive for specified minutes"""

async def cleanup_expired_busy_status():
    """Clear busy status for users whose wait_time has expired"""

async def get_online_users_count() -> int:
    """Get count of currently online users"""
```

#### Database Operations
- **Updates**: `user_status` table to set `is_online = FALSE`
- **Updates**: `user_status` table to clear expired busy statuses
- **Reads**: `user_status` table for online user counts

#### Impact on System
- Improves feed accuracy by showing only truly online users
- Prevents stale presence data from affecting user experience
- Maintains system performance by cleaning up expired states

---

### 3. Call Cleanup Service

**File**: `background_tasks/services/call_service.py`  
**Script**: `background_tasks/scripts/call_cleanup.py`  
**Schedule**: Every 10 minutes

#### Purpose
Cleans up expired calls that should have ended but are still marked as ongoing, ensuring proper call settlement and user status updates.

#### Functionality
- **Expired Call Detection**: Finds calls where user's wait_time has expired
- **Call Settlement**: Properly ends calls with accurate duration and earnings
- **Coin Accounting**: Ensures proper coin deduction and listener earnings
- **Status Updates**: Updates both caller and listener presence status
- **Redis Cleanup**: Removes call data from Redis cache

#### Key Functions
```python
async def cleanup_expired_calls():
    """Clean up expired calls and update presence status"""
    # Finds calls with expired wait_time
    # Calculates final duration and earnings
    # Updates call status and user presence
    # Cleans up Redis cache
```

#### Database Operations
- **Reads**: `user_calls` and `user_status` tables to find expired calls
- **Updates**: `user_calls` table with end time, duration, and earnings
- **Updates**: `user_wallets` table for listener earnings
- **Creates**: Transaction records for earnings
- **Updates**: `user_status` table for both users' presence

#### Financial Impact
- Ensures accurate billing for call duration
- Properly settles listener earnings
- Prevents revenue loss from unended calls
- Maintains accurate coin balances

---

### 4. Coin Deduction Service

**File**: `background_tasks/services/coin_deduction_service.py`  
**Script**: `background_tasks/scripts/coin_deduction.py`  
**Schedule**: Every minute

#### Purpose
Deducts coins from users every minute during ongoing calls, ensuring real-time billing and proper call termination when coins are insufficient.

#### Functionality
- **Per-Minute Billing**: Deducts coins every minute for ongoing calls
- **Balance Checking**: Verifies user has sufficient coins before deduction
- **Call Termination**: Ends calls when user runs out of coins
- **Earnings Calculation**: Calculates listener earnings based on actual payment
- **Redis Updates**: Updates call data in Redis cache

#### Key Functions
```python
async def deduct_per_minute_coins():
    """Deduct coins every minute for ongoing calls"""
    # Processes all ongoing calls
    # Deducts rate_per_minute for each call
    # Ends calls with insufficient coins
    # Updates Redis cache

async def process_call_coin_deduction(conn, call):
    """Process coin deduction for a single ongoing call"""

async def end_call_due_to_insufficient_coins(conn, call, current_balance):
    """End a call due to insufficient coins and settle properly"""
```

#### Database Operations
- **Reads**: `user_calls` table for ongoing calls
- **Reads**: `user_wallets` table for coin balances
- **Updates**: `user_wallets` table for coin deductions
- **Creates**: Transaction records for spending
- **Updates**: `user_calls` table with total coins spent
- **Updates**: `user_wallets` table for listener earnings

#### Call Rates
- **Audio Calls**: 30 coins per minute
- **Video Calls**: 60 coins per minute

#### Error Handling
- Gracefully handles insufficient coin scenarios
- Properly settles calls when users run out of coins
- Continues processing other calls if one fails
- Maintains data consistency with database transactions

---

## Setup and Installation

### Automated Setup

The easiest way to set up all background tasks is using the provided setup script:

```bash
# Make the setup script executable
chmod +x background_tasks/scripts/setup_cron.sh

# Run the setup script
./background_tasks/scripts/setup_cron.sh
```

This script will:
- Create log directory at `/var/log/saathii/`
- Set up all cron jobs with proper paths
- Make all Python scripts executable
- Test script execution
- Display current crontab entries

### Manual Setup

If you prefer to set up tasks manually:

1. **Create log directory**:
   ```bash
   sudo mkdir -p /var/log/saathii
   sudo chown $(whoami):$(whoami) /var/log/saathii
   ```

2. **Add cron jobs**:
   ```bash
   crontab -e
   ```
   
   Add these entries:
   ```cron
   # Badge assignment - daily at 12:01 AM
   1 0 * * * cd /path/to/saathii_backend_fastapi && python3 background_tasks/scripts/badge_assignment.py >> /var/log/saathii/badge_assignment.log 2>&1
   
   # Presence cleanup - every 5 minutes
   */5 * * * * cd /path/to/saathii_backend_fastapi && python3 background_tasks/scripts/presence_cleanup.py >> /var/log/saathii/presence_cleanup.log 2>&1
   
   # Call cleanup - every 10 minutes
   */10 * * * * cd /path/to/saathii_backend_fastapi && python3 background_tasks/scripts/call_cleanup.py >> /var/log/saathii/call_cleanup.log 2>&1
   
   # Coin deduction - every minute
   * * * * * cd /path/to/saathii_backend_fastapi && python3 background_tasks/scripts/coin_deduction.py >> /var/log/saathii/coin_deduction.log 2>&1
   
   # Log rotation - daily at 1:00 AM
   0 1 * * * find /var/log/saathii -name "*.log" -mtime +7 -delete
   ```

3. **Make scripts executable**:
   ```bash
   chmod +x background_tasks/scripts/*.py
   ```

## Manual Execution

You can run any background task manually for testing or debugging:

```bash
# Badge assignment
python3 background_tasks/scripts/badge_assignment.py

# Presence cleanup
python3 background_tasks/scripts/presence_cleanup.py

# Call cleanup
python3 background_tasks/scripts/call_cleanup.py

# Coin deduction
python3 background_tasks/scripts/coin_deduction.py
```

## Monitoring and Logs

### Log Files

All background tasks log their activities to `/var/log/saathii/`:

- `badge_assignment.log` - Badge assignment activities
- `presence_cleanup.log` - Presence cleanup activities  
- `call_cleanup.log` - Call cleanup activities
- `coin_deduction.log` - Coin deduction activities

### Viewing Logs

```bash
# View real-time logs
tail -f /var/log/saathii/badge_assignment.log
tail -f /var/log/saathii/presence_cleanup.log
tail -f /var/log/saathii/call_cleanup.log
tail -f /var/log/saathii/coin_deduction.log

# View recent logs
tail -n 100 /var/log/saathii/badge_assignment.log

# Search for errors
grep -i error /var/log/saathii/*.log
```

### Monitoring Commands

```bash
# Check if cron jobs are running
crontab -l | grep saathii

# Check recent cron activity
grep CRON /var/log/syslog | grep saathii

# Monitor system resources
htop
```

## Troubleshooting

### Common Issues

1. **Scripts not executing**:
   - Check if scripts are executable: `ls -la background_tasks/scripts/`
   - Verify cron jobs are installed: `crontab -l`
   - Check system logs: `grep CRON /var/log/syslog`

2. **Database connection errors**:
   - Ensure PostgreSQL is running
   - Check database connection settings
   - Verify environment variables are set

3. **Redis connection errors**:
   - Ensure Redis is running
   - Check Redis connection settings
   - Verify Redis is accessible

4. **Permission errors**:
   - Check log directory permissions: `ls -la /var/log/saathii/`
   - Ensure user has write access to log directory
   - Check script execution permissions

### Debug Mode

Run scripts with verbose logging:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 background_tasks/scripts/badge_assignment.py
```

### Health Checks

Create a simple health check script:

```bash
#!/bin/bash
# health_check.sh

echo "🔍 Checking Saathii Background Tasks Health..."

# Check if logs are being updated
echo "📊 Recent log activity:"
find /var/log/saathii -name "*.log" -mmin -60 -exec echo "✅ {} - Updated within last hour" \;

# Check cron jobs
echo "⏰ Active cron jobs:"
crontab -l | grep saathii

# Check database connectivity
echo "🗄️ Database connectivity:"
python3 -c "from api.clients.db import get_db_pool; import asyncio; asyncio.run(get_db_pool())" && echo "✅ Database OK" || echo "❌ Database Error"

# Check Redis connectivity  
echo "🔴 Redis connectivity:"
python3 -c "from api.clients.redis_client import redis_client; import asyncio; asyncio.run(redis_client.ping())" && echo "✅ Redis OK" || echo "❌ Redis Error"
```

## Performance Considerations

### Resource Usage

- **CPU**: Background tasks are lightweight and run briefly
- **Memory**: Minimal memory usage, tasks complete quickly
- **Database**: Tasks use connection pooling for efficiency
- **Redis**: Tasks clean up after themselves

### Optimization Tips

1. **Database Connections**: Tasks use connection pooling to minimize overhead
2. **Batch Processing**: Tasks process multiple records efficiently
3. **Error Handling**: Individual failures don't stop batch processing
4. **Log Rotation**: Automatic cleanup prevents disk space issues

### Scaling Considerations

- Tasks are designed to handle high user loads
- Database queries are optimized for performance
- Redis operations are minimal and efficient
- Cron scheduling prevents task overlap

## Security Considerations

### Access Control

- Scripts run with appropriate user permissions
- Database connections use secure credentials
- Log files are protected with proper permissions

### Data Protection

- Sensitive data is not logged
- Database transactions ensure data consistency
- Error handling prevents data corruption

### Monitoring

- All activities are logged for audit purposes
- Error conditions are tracked and reported
- Performance metrics are available for analysis

## Maintenance

### Regular Tasks

1. **Monitor log files** for errors and performance issues
2. **Check cron job status** regularly
3. **Review database performance** for background task queries
4. **Clean up old logs** (automated with log rotation)

### Updates

When updating the codebase:

1. **Test scripts manually** before deploying
2. **Update cron jobs** if script paths change
3. **Monitor logs** after deployment
4. **Verify all tasks** are running correctly

### Backup Considerations

- Log files contain important operational data
- Consider backing up logs for audit purposes
- Database backups should include all tables used by background tasks

---

## Summary

The background task system is essential for maintaining the health and accuracy of the Saathii Backend API. These tasks ensure:

- **Accurate user presence** through regular cleanup
- **Proper call billing** through per-minute coin deduction
- **Fair listener compensation** through badge-based earnings
- **System reliability** through automated maintenance

Proper setup and monitoring of these tasks is crucial for the smooth operation of the Saathii application.
