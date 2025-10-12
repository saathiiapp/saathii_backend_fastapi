# Background Tasks API Reference

This document provides a comprehensive reference for the background task services that can be called programmatically from within the Saathii Backend API.

## Overview

The background task system provides programmatic access to all background services through Python modules. These services can be imported and used in your application code for testing, debugging, or custom automation.

## Service Modules

### 1. Badge Assignment Service

**Module**: `background_tasks.services.badge_service`  
**Purpose**: Assign daily badges to listeners based on performance

#### Functions

##### `assign_daily_badges()`

Assigns badges for today based on yesterday's performance.

```python
from background_tasks.services.badge_service import assign_daily_badges

# Assign badges for all listeners
stats = await assign_daily_badges()
```

**Returns**: `dict` - Statistics about badge assignments
```python
{
    "total_listeners": 150,
    "basic_assigned": 45,
    "bronze_assigned": 60,
    "silver_assigned": 30,
    "gold_assigned": 15,
    "errors": 0
}
```

**Raises**: `Exception` - If badge assignment fails

**Example Usage**:
```python
import asyncio
from background_tasks.services.badge_service import assign_daily_badges

async def main():
    try:
        stats = await assign_daily_badges()
        print(f"Badge assignment completed: {stats}")
    except Exception as e:
        print(f"Badge assignment failed: {e}")

# Run the function
asyncio.run(main())
```

---

### 2. Presence Cleanup Service

**Module**: `background_tasks.services.presence_service`  
**Purpose**: Clean up user presence data and mark inactive users offline

#### Functions

##### `mark_inactive_users_offline(inactive_minutes: int = 5)`

Marks users as offline if they haven't been seen for the specified number of minutes.

```python
from background_tasks.services.presence_service import mark_inactive_users_offline

# Mark users offline after 5 minutes of inactivity
result = await mark_inactive_users_offline(inactive_minutes=5)
```

**Parameters**:
- `inactive_minutes` (int): Number of minutes of inactivity before marking offline (default: 5)

**Returns**: `int` - Number of users marked as offline

**Example Usage**:
```python
import asyncio
from background_tasks.services.presence_service import mark_inactive_users_offline

async def main():
    # Mark users offline after 10 minutes
    count = await mark_inactive_users_offline(inactive_minutes=10)
    print(f"Marked {count} users as offline")

asyncio.run(main())
```

##### `cleanup_expired_busy_status()`

Clears busy status for users whose wait_time has expired.

```python
from background_tasks.services.presence_service import cleanup_expired_busy_status

# Clear expired busy statuses
result = await cleanup_expired_busy_status()
```

**Returns**: `int` - Number of expired busy statuses cleared

**Example Usage**:
```python
import asyncio
from background_tasks.services.presence_service import cleanup_expired_busy_status

async def main():
    count = await cleanup_expired_busy_status()
    print(f"Cleared {count} expired busy statuses")

asyncio.run(main())
```

##### `get_online_users_count()`

Gets the count of currently online users.

```python
from background_tasks.services.presence_service import get_online_users_count

# Get online user count
count = await get_online_users_count()
```

**Returns**: `int` - Number of currently online users

**Example Usage**:
```python
import asyncio
from background_tasks.services.presence_service import get_online_users_count

async def main():
    count = await get_online_users_count()
    print(f"Currently online users: {count}")

asyncio.run(main())
```

---

### 3. Call Cleanup Service

**Module**: `background_tasks.services.call_service`  
**Purpose**: Clean up expired calls and update presence status

#### Functions

##### `cleanup_expired_calls()`

Cleans up expired calls and updates presence status.

```python
from background_tasks.services.call_service import cleanup_expired_calls

# Clean up expired calls
await cleanup_expired_calls()
```

**Returns**: `None`

**Side Effects**:
- Updates expired calls in the database
- Settles listener earnings
- Updates user presence status
- Cleans up Redis cache

**Example Usage**:
```python
import asyncio
from background_tasks.services.call_service import cleanup_expired_calls

async def main():
    try:
        await cleanup_expired_calls()
        print("Call cleanup completed successfully")
    except Exception as e:
        print(f"Call cleanup failed: {e}")

asyncio.run(main())
```

##### `get_user_coin_balance(user_id: int)`

Gets a user's current coin balance.

```python
from background_tasks.services.call_service import get_user_coin_balance

# Get user's coin balance
balance = await get_user_coin_balance(user_id=123)
```

**Parameters**:
- `user_id` (int): The user's ID

**Returns**: `int` - User's current coin balance

**Example Usage**:
```python
import asyncio
from background_tasks.services.call_service import get_user_coin_balance

async def main():
    balance = await get_user_coin_balance(user_id=123)
    print(f"User 123 has {balance} coins")

asyncio.run(main())
```

##### `update_user_coin_balance(user_id: int, amount: int, operation: str = "subtract", tx_type: str = "spend")`

Updates a user's coin balance and creates transaction records.

```python
from background_tasks.services.call_service import update_user_coin_balance

# Subtract 50 coins from user
await update_user_coin_balance(user_id=123, amount=50, operation="subtract", tx_type="spend")

# Add 100 coins to user
await update_user_coin_balance(user_id=123, amount=100, operation="add", tx_type="earn")
```

**Parameters**:
- `user_id` (int): The user's ID
- `amount` (int): Amount of coins to add/subtract
- `operation` (str): "subtract" or "add" (default: "subtract")
- `tx_type` (str): Transaction type (default: "spend")

**Raises**: `ValueError` - If insufficient coins for subtraction

**Example Usage**:
```python
import asyncio
from background_tasks.services.call_service import update_user_coin_balance

async def main():
    try:
        # Subtract coins
        await update_user_coin_balance(user_id=123, amount=50, operation="subtract", tx_type="spend")
        print("Coins subtracted successfully")
        
        # Add coins
        await update_user_coin_balance(user_id=123, amount=100, operation="add", tx_type="earn")
        print("Coins added successfully")
    except ValueError as e:
        print(f"Insufficient coins: {e}")

asyncio.run(main())
```

---

### 4. Coin Deduction Service

**Module**: `background_tasks.services.coin_deduction_service`  
**Purpose**: Deduct coins per minute for ongoing calls

#### Functions

##### `deduct_per_minute_coins()`

Deducts coins every minute for ongoing calls.

```python
from background_tasks.services.coin_deduction_service import deduct_per_minute_coins

# Deduct coins for all ongoing calls
await deduct_per_minute_coins()
```

**Returns**: `None`

**Side Effects**:
- Deducts coins from users with ongoing calls
- Ends calls when users run out of coins
- Updates Redis cache
- Settles listener earnings

**Example Usage**:
```python
import asyncio
from background_tasks.services.coin_deduction_service import deduct_per_minute_coins

async def main():
    try:
        await deduct_per_minute_coins()
        print("Coin deduction completed successfully")
    except Exception as e:
        print(f"Coin deduction failed: {e}")

asyncio.run(main())
```

##### `process_call_coin_deduction(conn, call)`

Processes coin deduction for a single ongoing call.

```python
from background_tasks.services.coin_deduction_service import process_call_coin_deduction

# Process coin deduction for a specific call
await process_call_coin_deduction(conn, call_data)
```

**Parameters**:
- `conn`: Database connection object
- `call`: Call data dictionary

**Returns**: `None`

**Example Usage**:
```python
import asyncio
from background_tasks.services.coin_deduction_service import process_call_coin_deduction
from api.clients.db import get_db_pool

async def main():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get a specific call
        call = await conn.fetchrow("SELECT * FROM user_calls WHERE call_id = $1", call_id)
        if call:
            await process_call_coin_deduction(conn, call)

asyncio.run(main())
```

##### `end_call_due_to_insufficient_coins(conn, call, current_balance)`

Ends a call due to insufficient coins and settles properly.

```python
from background_tasks.services.coin_deduction_service import end_call_due_to_insufficient_coins

# End call due to insufficient coins
await end_call_due_to_insufficient_coins(conn, call_data, current_balance)
```

**Parameters**:
- `conn`: Database connection object
- `call`: Call data dictionary
- `current_balance`: User's current coin balance

**Returns**: `None`

**Example Usage**:
```python
import asyncio
from background_tasks.services.coin_deduction_service import end_call_due_to_insufficient_coins
from api.clients.db import get_db_pool

async def main():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        call = await conn.fetchrow("SELECT * FROM user_calls WHERE call_id = $1", call_id)
        balance = await get_user_coin_balance(call['user_id'])
        await end_call_due_to_insufficient_coins(conn, call, balance)

asyncio.run(main())
```

## Integration Examples

### 1. Custom Background Task

Create a custom background task that combines multiple services:

```python
import asyncio
import logging
from background_tasks.services.presence_service import mark_inactive_users_offline, cleanup_expired_busy_status
from background_tasks.services.call_service import cleanup_expired_calls
from background_tasks.services.coin_deduction_service import deduct_per_minute_coins

logger = logging.getLogger(__name__)

async def custom_maintenance_task():
    """Custom maintenance task that runs multiple cleanup operations"""
    try:
        logger.info("Starting custom maintenance task")
        
        # Run all cleanup tasks in parallel
        results = await asyncio.gather(
            mark_inactive_users_offline(inactive_minutes=5),
            cleanup_expired_busy_status(),
            cleanup_expired_calls(),
            deduct_per_minute_coins(),
            return_exceptions=True
        )
        
        # Log results
        logger.info(f"Maintenance task completed: {results}")
        
    except Exception as e:
        logger.error(f"Maintenance task failed: {e}")

# Run the custom task
asyncio.run(custom_maintenance_task())
```

### 2. Health Check Integration

Integrate background task health checks into your application:

```python
import asyncio
from background_tasks.services.presence_service import get_online_users_count
from background_tasks.services.call_service import get_user_coin_balance

async def health_check():
    """Health check that verifies background task functionality"""
    try:
        # Check online users
        online_count = await get_online_users_count()
        print(f"Online users: {online_count}")
        
        # Check a specific user's balance
        balance = await get_user_coin_balance(user_id=1)
        print(f"User 1 balance: {balance}")
        
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

# Run health check
health_status = asyncio.run(health_check())
```

### 3. Testing Integration

Use background task services in your tests:

```python
import pytest
import asyncio
from background_tasks.services.badge_service import assign_daily_badges
from background_tasks.services.presence_service import mark_inactive_users_offline

@pytest.mark.asyncio
async def test_badge_assignment():
    """Test badge assignment functionality"""
    stats = await assign_daily_badges()
    
    assert stats['total_listeners'] >= 0
    assert stats['errors'] == 0
    assert 'basic_assigned' in stats

@pytest.mark.asyncio
async def test_presence_cleanup():
    """Test presence cleanup functionality"""
    count = await mark_inactive_users_offline(inactive_minutes=1)
    
    assert count >= 0
```

## Error Handling

### Common Exceptions

All background task services can raise these exceptions:

- **`ValueError`**: Invalid parameters or insufficient coins
- **`ConnectionError`**: Database or Redis connection issues
- **`Exception`**: General errors during task execution

### Error Handling Best Practices

```python
import asyncio
import logging
from background_tasks.services.badge_service import assign_daily_badges

logger = logging.getLogger(__name__)

async def safe_badge_assignment():
    """Safely run badge assignment with proper error handling"""
    try:
        stats = await assign_daily_badges()
        logger.info(f"Badge assignment successful: {stats}")
        return stats
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return None
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

# Run with error handling
result = asyncio.run(safe_badge_assignment())
```

## Performance Considerations

### Database Connections

Background task services use connection pooling for efficiency:

```python
from api.clients.db import get_db_pool

async def efficient_task():
    """Example of efficient database usage"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Use the connection for multiple operations
        result1 = await conn.fetchval("SELECT COUNT(*) FROM users")
        result2 = await conn.fetchval("SELECT COUNT(*) FROM calls")
        return result1, result2
```

### Async Operations

All background task services are async and should be awaited:

```python
# Correct usage
result = await assign_daily_badges()

# Incorrect usage (will not work)
result = assign_daily_badges()
```

### Resource Cleanup

Always clean up resources after use:

```python
async def cleanup_example():
    """Example of proper resource cleanup"""
    pool = await get_db_pool()
    try:
        # Use the pool
        async with pool.acquire() as conn:
            # Do work
            pass
    finally:
        # Clean up
        await pool.close()
```

## Monitoring and Logging

### Logging Configuration

Configure logging for background task services:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get logger for background tasks
logger = logging.getLogger('background_tasks')

# Use in your code
logger.info("Starting background task")
```

### Performance Monitoring

Monitor background task performance:

```python
import time
import asyncio
from background_tasks.services.badge_service import assign_daily_badges

async def monitored_badge_assignment():
    """Monitor badge assignment performance"""
    start_time = time.time()
    
    try:
        stats = await assign_daily_badges()
        end_time = time.time()
        
        print(f"Badge assignment completed in {end_time - start_time:.2f} seconds")
        print(f"Stats: {stats}")
        
    except Exception as e:
        end_time = time.time()
        print(f"Badge assignment failed after {end_time - start_time:.2f} seconds: {e}")

asyncio.run(monitored_badge_assignment())
```

## Conclusion

The background task services provide a powerful API for programmatic access to all background functionality. Use these services to:

- **Test** background task functionality
- **Debug** issues with automated tasks
- **Create** custom maintenance scripts
- **Integrate** background tasks into your application
- **Monitor** system health and performance

Always handle errors properly and use async/await patterns for optimal performance.
