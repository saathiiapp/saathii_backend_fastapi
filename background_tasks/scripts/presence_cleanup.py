#!/usr/bin/env python3
"""
Presence Cleanup Script
Runs every 5 minutes to clean up inactive users and expired busy status
"""
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from background_tasks.services.presence_service import mark_inactive_users_offline, cleanup_expired_busy_status
from app.clients.db import get_db_pool

async def main():
    """Main function to cleanup presence data"""
    try:
        print(f"🧹 Starting presence cleanup at {datetime.now()}")
        
        # Mark inactive users as offline (5 minutes threshold)
        inactive_result = await mark_inactive_users_offline(inactive_minutes=5)
        print(f"   Marked {inactive_result} users as offline")
        
        # Clean up expired busy status
        busy_result = await cleanup_expired_busy_status()
        print(f"   Cleared {busy_result} expired busy statuses")
        
        print("✅ Presence cleanup completed successfully")
        return 0
        
    except Exception as e:
        print(f"❌ Error during presence cleanup: {e}")
        return 1
    finally:
        # Close database connections
        pool = await get_db_pool()
        await pool.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
