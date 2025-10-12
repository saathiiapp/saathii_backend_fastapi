---
sidebar_position: 1
---

# Background Tasks

The Saathii Backend API includes a comprehensive background task system that runs automatically to maintain system health, process payments, and manage user presence.

## Overview

The background task system consists of four core services that work together to ensure the smooth operation of the Saathii application:

- **Badge Assignment** - Assigns daily badges to listeners based on performance
- **Presence Cleanup** - Maintains accurate user presence status
- **Call Cleanup** - Cleans up expired calls and settles billing
- **Coin Deduction** - Real-time billing for ongoing calls

## Documentation

### 📚 Main Documentation
- **[Background Tasks Overview](./background-tasks)** - Complete system overview and setup guide
- **[API Reference](./background-tasks-api)** - Programmatic API reference for developers
- **[Summary & Quick Reference](./background-tasks-summary)** - Comprehensive summary and troubleshooting guide

### 🛠️ Setup Guides
- **[Background Tasks Setup Guide](../guides/background-tasks-setup)** - Detailed setup and maintenance instructions

## Quick Start

1. **Automated Setup** (Recommended):
   ```bash
   chmod +x background_tasks/scripts/setup_cron.sh
   ./background_tasks/scripts/setup_cron.sh
   ```

2. **Manual Setup**:
   - Create log directory: `sudo mkdir -p /var/log/saathii`
   - Make scripts executable: `chmod +x background_tasks/scripts/*.py`
   - Add cron jobs: `crontab -e`

3. **Verify Setup**:
   ```bash
   crontab -l | grep saathii
   python3 background_tasks/scripts/badge_assignment.py
   ```

## Task Schedule

| Task | Frequency | Purpose |
|------|-----------|---------|
| Badge Assignment | Daily (12:01 AM) | Assign listener badges |
| Presence Cleanup | Every 5 minutes | Mark inactive users offline |
| Call Cleanup | Every 10 minutes | Clean expired calls |
| Coin Deduction | Every minute | Deduct coins for calls |

## Monitoring

Monitor your background tasks:

```bash
# View real-time logs
tail -f /var/log/saathii/badge_assignment.log
tail -f /var/log/saathii/presence_cleanup.log
tail -f /var/log/saathii/call_cleanup.log
tail -f /var/log/saathii/coin_deduction.log

# Check cron jobs
crontab -l | grep saathii
```

## Need Help?

- Check the [Troubleshooting Guide](./background-tasks-summary#troubleshooting)
- Review the [Setup Guide](../guides/background-tasks-setup)
- Examine the [API Reference](./background-tasks-api) for programmatic usage
