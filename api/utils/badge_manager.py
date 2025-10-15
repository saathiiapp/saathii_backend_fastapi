"""
Badge management utilities for listener earnings
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Tuple, Optional
from api.clients.db import get_db_pool

# Badge configuration based on daily call duration
BADGE_THRESHOLDS = {
    'basic': 0,      # Default - 0 hours
    'bronze': 3,     # 3+ hours
    'silver': 6,     # 6+ hours  
    'gold': 9        # 9+ hours
}

# Earning rates per badge (INR per minute)
BADGE_RATES = {
    'basic': {
        'audio': 1.0,
        'video': 6.0
    },
    'bronze': {
        'audio': 1.25,
        'video': 7.0
    },
    'silver': {
        'audio': 1.5,
        'video': 8.5
    },
    'gold': {
        'audio': 1.8,
        'video': 10.0
    }
}

async def calculate_daily_call_duration(listener_id: int, target_date: date) -> float:
    """
    Calculate total call duration in hours for a listener on a specific date
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(duration_minutes), 0) as total_minutes
            FROM user_calls 
            WHERE listener_id = $1 
            AND DATE(start_time) = $2 
            AND status = 'completed'
            """,
            listener_id, target_date
        )
        
        if result:
            return result['total_minutes'] / 60.0  # Convert minutes to hours
        return 0.0

async def determine_badge_for_duration(duration_hours: float) -> str:
    """
    Determine badge based on call duration
    """
    if duration_hours >= BADGE_THRESHOLDS['gold']:
        return 'gold'
    elif duration_hours >= BADGE_THRESHOLDS['silver']:
        return 'silver'
    elif duration_hours >= BADGE_THRESHOLDS['bronze']:
        return 'bronze'
    else:
        return 'basic'

async def assign_badge_for_date(listener_id: int, target_date: date) -> Optional[Dict]:
    """
    Assign badge for a specific date based on previous day's performance
    """
    # Calculate duration for the previous day
    previous_date = target_date - timedelta(days=1)
    duration_hours = await calculate_daily_call_duration(listener_id, previous_date)
    
    # Determine badge
    badge = await determine_badge_for_duration(duration_hours)
    
    # Get rates for the badge
    audio_rate = BADGE_RATES[badge]['audio']
    video_rate = BADGE_RATES[badge]['video']
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Insert or update badge assignment
        result = await conn.fetchrow(
            """
            INSERT INTO listener_badges 
            (listener_id, date, badge, audio_rate_per_minute, video_rate_per_minute, assigned_at)
            VALUES ($1, $2, $3, $4, $5, now())
            ON CONFLICT (listener_id, date) 
            DO UPDATE SET 
                badge = EXCLUDED.badge,
                audio_rate_per_minute = EXCLUDED.audio_rate_per_minute,
                video_rate_per_minute = EXCLUDED.video_rate_per_minute,
                updated_at = now()
            RETURNING *
            """,
            listener_id, target_date, badge, audio_rate, video_rate
        )
        
        return dict(result) if result else None

async def get_listener_badge_for_date(listener_id: int, target_date: date) -> Optional[Dict]:
    """
    Get listener's badge for a specific date
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT * FROM listener_badges 
            WHERE listener_id = $1 AND date = $2
            """,
            listener_id, target_date
        )
        
        return dict(result) if result else None

async def get_current_listener_badge(listener_id: int) -> Optional[Dict]:
    """
    Get listener's current badge (today's badge)
    """
    today = date.today()
    return await get_listener_badge_for_date(listener_id, today)

async def assign_badges_for_all_listeners(target_date: date) -> Dict[str, int]:
    """
    Assign badges for all listeners for a specific date
    Returns statistics about the assignment process
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get all users with listener role
        listeners = await conn.fetch(
            """
            SELECT ur.user_id 
            FROM user_roles ur 
            WHERE ur.role = 'listener'
            """
        )
        
        stats = {
            'total_listeners': len(listeners),
            'basic_assigned': 0,
            'bronze_assigned': 0,
            'silver_assigned': 0,
            'gold_assigned': 0,
            'errors': 0
        }
        
        for listener in listeners:
            try:
                badge_data = await assign_badge_for_date(listener['user_id'], target_date)
                if badge_data:
                    stats[f"{badge_data['badge']}_assigned"] += 1
                else:
                    stats['errors'] += 1
            except Exception as e:
                print(f"Error assigning badge for listener {listener['user_id']}: {e}")
                stats['errors'] += 1
        
        return stats

async def get_listener_earning_rate(listener_id: int, call_type: str, target_date: date = None) -> float:
    """
    Get the earning rate for a listener based on their badge for a specific date
    """
    if target_date is None:
        target_date = date.today()
    
    badge_data = await get_listener_badge_for_date(listener_id, target_date)
    
    if not badge_data:
        # If no badge assigned, use basic rates
        return BADGE_RATES['basic'][call_type]
    
    if call_type == 'audio':
        return float(badge_data['audio_rate_per_minute'])
    elif call_type == 'video':
        return float(badge_data['video_rate_per_minute'])
    else:
        return BADGE_RATES['basic'][call_type]

async def assign_basic_badge_for_today(listener_id: int) -> Optional[Dict]:
    """
    Assign Basic badge to a new listener for today
    This is used when a new listener registers
    """
    today = date.today()
    badge = 'basic'
    audio_rate = BADGE_RATES[badge]['audio']
    video_rate = BADGE_RATES[badge]['video']
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Insert Basic badge for today
        result = await conn.fetchrow(
            """
            INSERT INTO listener_badges 
            (listener_id, date, badge, audio_rate_per_minute, video_rate_per_minute, assigned_at)
            VALUES ($1, $2, $3, $4, $5, now())
            ON CONFLICT (listener_id, date) 
            DO UPDATE SET 
                badge = EXCLUDED.badge,
                audio_rate_per_minute = EXCLUDED.audio_rate_per_minute,
                video_rate_per_minute = EXCLUDED.video_rate_per_minute,
                updated_at = now()
            RETURNING *
            """,
            listener_id, today, badge, audio_rate, video_rate
        )
        
        return dict(result) if result else None
