#!/usr/bin/env python3
"""
Coin Deduction Script
Runs every minute to deduct coins from users during active calls
"""
import asyncio
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from background_tasks.services.coin_deduction_service import deduct_per_minute_coins
from api.clients.db import get_db_pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to deduct per-minute coins for ongoing calls"""
    try:
        logger.info(f"💰 Starting per-minute coin deduction at {datetime.now()}")
        
        # Deduct coins for ongoing calls
        await deduct_per_minute_coins()
        
        logger.info("✅ Per-minute coin deduction completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error during per-minute coin deduction: {e}")
        return 1
    finally:
        # Close database connections
        pool = await get_db_pool()
        await pool.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
