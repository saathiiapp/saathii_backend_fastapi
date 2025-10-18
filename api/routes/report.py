from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.utils.user_validation import validate_customer_or_verified_listener
from api.schemas.report import (
    ReportUserRequest,
    ReportActionResponse,
    ReportedUser,
    ReportedUsersResponse,
    AdminReportedUser,
    AdminReportedUsersResponse,
)


router = APIRouter(tags=["Reporting"])


async def get_current_user_async(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    
    # Validate user is active
    user_id = payload.get("user_id")
    
    # Validate user is active customer or verified listener
    await validate_customer_or_verified_listener(user_id)
    
    return payload


@router.post("/both/report", response_model=ReportActionResponse)
async def report_user(
    data: ReportUserRequest,
    user=Depends(get_current_user_async)
):
    """Report a user (customer or listener)."""
    user_id = user["user_id"]
    reported_id = data.reported_id
    reason = data.reason

    if user_id == reported_id:
        raise HTTPException(status_code=400, detail="Cannot report yourself")

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if user to be reported exists
        reported_user = await conn.fetchrow(
            "SELECT user_id, username FROM users WHERE user_id = $1",
            reported_id
        )

        if not reported_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if already reported
        existing = await conn.fetchrow(
            "SELECT blocker_id FROM user_blocks WHERE blocker_id = $1 AND blocked_id = $2 AND action_type = 'report'",
            user_id, reported_id
        )

        if existing:
            return ReportActionResponse(
                success=True,
                message=f"Already reported {reported_user['username'] or 'this user'}",
                reported_id=reported_id,
                is_reported=True
            )

        # Report the user
        await conn.execute(
            """
            INSERT INTO user_blocks (blocker_id, blocked_id, action_type, reason, created_at)
            VALUES ($1, $2, $3, $4, now())
            """,
            user_id, reported_id, "report", reason
        )

        return ReportActionResponse(
            success=True,
            message=f"Successfully reported {reported_user['username'] or 'user'}",
            reported_id=reported_id,
            is_reported=True
        )


@router.get("/both/reported", response_model=ReportedUsersResponse)
async def get_reported_users(
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user_async)
):
    """Get list of users reported by current user (customer or listener)."""
    user_id = user["user_id"]

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    offset = (page - 1) * per_page

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        base_query = """
            FROM user_blocks ub
            JOIN users u ON ub.blocked_id = u.user_id
            WHERE ub.blocker_id = $1 AND ub.action_type = 'report'
        """
        params = [user_id]

        count_query = f"SELECT COUNT(*) {base_query}"
        total_count = await conn.fetchval(count_query, *params)

        reported_query = f"""
            SELECT 
                u.user_id,
                u.username,
                u.sex,
                u.bio,
                u.profile_image_url,
                ub.reason,
                ub.created_at as reported_at
            {base_query}
            ORDER BY ub.created_at DESC
            LIMIT $2 OFFSET $3
        """
        params.extend([per_page, offset])

        reported_users = await conn.fetch(reported_query, *params)

        reported_list = []
        for reported in reported_users:
            reported_list.append(ReportedUser(
                user_id=reported['user_id'],
                username=reported['username'],
                sex=reported['sex'],
                bio=reported['bio'],
                profile_image_url=reported['profile_image_url'],
                reason=reported['reason'],
                reported_at=reported['reported_at']
            ))

        has_next = offset + per_page < total_count
        has_previous = page > 1

        return ReportedUsersResponse(
            reported_users=reported_list,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous
        )


@router.get("/admin/reports", response_model=AdminReportedUsersResponse)
async def get_all_reports_admin(
    page: int = 1,
    per_page: int = 20,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Get all reports with date filters (no authentication required)."""
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    offset = (page - 1) * per_page

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Build dynamic query with filters
        base_query = """
            FROM user_blocks ub
            JOIN users reporter ON ub.blocker_id = reporter.user_id
            JOIN users reported ON ub.blocked_id = reported.user_id
            WHERE ub.action_type = 'report'
        """
        params = []
        param_count = 0

        # Add date filters
        if date_from:
            param_count += 1
            base_query += f" AND ub.created_at >= ${param_count}"
            params.append(date_from)

        if date_to:
            param_count += 1
            base_query += f" AND ub.created_at <= ${param_count}"
            params.append(date_to)

        # Get total count
        count_query = f"SELECT COUNT(*) {base_query}"
        total_count = await conn.fetchval(count_query, *params)

        # Get reports with pagination
        reports_query = f"""
            SELECT 
                CONCAT(ub.blocker_id, '-', ub.blocked_id, '-', EXTRACT(EPOCH FROM ub.created_at)::BIGINT) as report_id,
                ub.blocker_id as reporter_id,
                reporter.username as reporter_username,
                ub.blocked_id as reported_id,
                reported.username as reported_username,
                reported.sex as reported_sex,
                reported.bio as reported_bio,
                reported.profile_image_url as reported_profile_image_url,
                ub.reason,
                ub.created_at as reported_at
            {base_query}
            ORDER BY ub.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([per_page, offset])

        reports = await conn.fetch(reports_query, *params)

        reports_list = []
        for report in reports:
            reports_list.append(AdminReportedUser(
                report_id=report['report_id'],
                reporter_id=report['reporter_id'],
                reporter_username=report['reporter_username'],
                reported_id=report['reported_id'],
                reported_username=report['reported_username'],
                reported_sex=report['reported_sex'],
                reported_bio=report['reported_bio'],
                reported_profile_image_url=report['reported_profile_image_url'],
                reason=report['reason'],
                reported_at=report['reported_at']
            ))

        has_next = offset + per_page < total_count
        has_previous = page > 1

        return AdminReportedUsersResponse(
            reported_users=reports_list,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous
        )
