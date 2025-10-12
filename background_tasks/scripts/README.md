# Saathii Backend Scripts

Essential scheduled tasks for the Saathii Backend application.

## Scripts

- **`badge_assignment.py`** - Daily badge assignment (12:01 AM)
- **`presence_cleanup.py`** - Clean up inactive users (every 5 minutes)  
- **`call_cleanup.py`** - Clean up expired calls (every 10 minutes)
- **`setup_cron.sh`** - Setup cron jobs

## Quick Setup

```bash
chmod +x scripts/setup_cron.sh
./scripts/setup_cron.sh
```

## Manual Execution

```bash
python3 scripts/badge_assignment.py
python3 scripts/presence_cleanup.py
python3 scripts/call_cleanup.py
```
