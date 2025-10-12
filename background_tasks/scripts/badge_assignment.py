#!/usr/bin/env python3
"""
Badge Assignment Script
Runs daily at 12:01 AM to assign badges to listeners based on their previous day's performance
"""
import asyncio
import sys
import os
from datetime import date, datetime
from pathlib import Path

# Add the api directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from background_tasks.services.badge_service import assign_daily_badges
from api.clients.db import get_db_pool

async def main():
    """Main function to assign badges for today"""
    try:
        today = date.today()
        print(f"🏆 Starting badge assignment for {today}")
        
        # Assign badges for all listeners
        stats = await assign_daily_badges()
        
        print(f"✅ Badge assignment completed for {today}:")
        print(f"   Total listeners: {stats['total_listeners']}")
        print(f"   Basic: {stats['basic_assigned']}")
        print(f"   Bronze: {stats['bronze_assigned']}")
        print(f"   Silver: {stats['silver_assigned']}")
        print(f"   Gold: {stats['gold_assigned']}")
        print(f"   Errors: {stats['errors']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during badge assignment: {e}")
        return 1
    finally:
        # Close database connections
        pool = await get_db_pool()
        await pool.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
