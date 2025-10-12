#!/usr/bin/env python3
"""
Call Cleanup Script
Runs every 10 minutes to clean up expired calls and update presence status
"""
import asyncio
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add the api directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from background_tasks.services.call_service import cleanup_expired_calls
from api.clients.db import get_db_pool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main function to cleanup expired calls"""
    try:
        logger.info(f"🧹 Starting call cleanup at {datetime.now()}")
        
        # Clean up expired calls
        await cleanup_expired_calls()
        
        logger.info("✅ Call cleanup completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error during call cleanup: {e}")
        return 1
    finally:
        # Close database connections
        pool = await get_db_pool()
        await pool.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
