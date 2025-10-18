from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import List, Optional
from datetime import datetime
from api.clients.db import get_db_pool
from api.clients.jwt_handler import decode_jwt
from api.clients.redis_client import redis_client
from api.utils.user_validation import validate_customer_or_verified_listener
from api.schemas.help_support import (
    CreateSupportTicketRequest,
    SupportTicketResponse,
    SupportTicketListResponse,
    AdminSupportTicketResponse,
    AdminSupportTicketListResponse,
    IssueTypeEnum,
    SupportStatusEnum
)

router = APIRouter(tags=["Help & Support"])


async def get_current_user_async(authorization: str = Header(...)):
    """Get current authenticated user and validate they are active customer or verified listener."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    
    # Reject if blacklisted (scoped by user id and access jti)
    user_id = payload.get("user_id")
    jti = payload.get("jti")
    if user_id and jti and await redis_client.get(f"access:{user_id}:{jti}"):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    # Validate user is active customer or verified listener
    await validate_customer_or_verified_listener(user_id)
    
    return payload


@router.post("/both/support/tickets", response_model=SupportTicketResponse)
async def create_support_ticket(
    request: CreateSupportTicketRequest,
    user=Depends(get_current_user_async)
):
    """
    Create a new support ticket.
    
    Validation rules:
    - call_session_support: call_id is required
    - payment_support: transaction_id is required
    - other: no additional fields required
    
    Available to:
    - Active customers
    - Active and verified listeners
    """
    user_id = user["user_id"]
    
    # Validate required fields based on issue type
    if request.issue_type == IssueTypeEnum.call_session_support:
        if not request.call_id:
            raise HTTPException(
                status_code=400, 
                detail="call_id is required for call_session_support issues"
            )
    elif request.issue_type == IssueTypeEnum.payment_support:
        if not request.transaction_id:
            raise HTTPException(
                status_code=400, 
                detail="transaction_id is required for payment_support issues"
            )
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Validate call_id exists and belongs to user (if provided)
        if request.call_id:
            call_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM user_calls WHERE call_id = $1 AND user_id = $2)",
                request.call_id, user_id
            )
            if not call_exists:
                raise HTTPException(
                    status_code=400,
                    detail="Call not found or does not belong to user"
                )
        
        # Validate transaction_id exists and belongs to user (if provided)
        if request.transaction_id:
            transaction_exists = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM user_transactions ut
                    JOIN user_wallets uw ON ut.wallet_id = uw.wallet_id
                    WHERE ut.transaction_id = $1 AND uw.user_id = $2
                )
                """,
                request.transaction_id, user_id
            )
            if not transaction_exists:
                raise HTTPException(
                    status_code=400,
                    detail="Transaction not found or does not belong to user"
                )
        
        # Insert the support ticket
        support_ticket = await conn.fetchrow(
            """
            INSERT INTO help_support (
                user_id, issue_type, issue, description, 
                image_s3_urls, require_call, call_id, transaction_id, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active')
            RETURNING 
                support_id, user_id, issue_type, issue, description,
                image_s3_urls, require_call, call_id, transaction_id, status, admin_notes,
                resolved_at, created_at, updated_at
            """,
            user_id,
            request.issue_type.value,
            request.issue,
            request.description,
            request.image_s3_urls or [],
            request.require_call,
            request.call_id,
            request.transaction_id
        )
        
        if not support_ticket:
            raise HTTPException(status_code=500, detail="Failed to create support ticket")
        
        return SupportTicketResponse(
            support_id=support_ticket["support_id"],
            user_id=support_ticket["user_id"],
            issue_type=IssueTypeEnum(support_ticket["issue_type"]),
            issue=support_ticket["issue"],
            description=support_ticket["description"],
            image_s3_urls=support_ticket["image_s3_urls"] or [],
            require_call=support_ticket["require_call"],
            call_id=support_ticket["call_id"],
            transaction_id=support_ticket["transaction_id"],
            status=SupportStatusEnum(support_ticket["status"]),
            admin_notes=support_ticket["admin_notes"],
            resolved_at=support_ticket["resolved_at"],
            created_at=support_ticket["created_at"],
            updated_at=support_ticket["updated_at"]
        )


@router.get("/both/support/tickets", response_model=SupportTicketListResponse)
async def get_my_support_tickets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Number of tickets per page"),
    status: Optional[SupportStatusEnum] = Query(None, description="Filter by ticket status"),
    issue_type: Optional[IssueTypeEnum] = Query(None, description="Filter by issue type"),
    user=Depends(get_current_user_async)
):
    """
    Get support tickets for the current user.
    
    Available to:
    - Active customers
    - Active and verified listeners
    """
    user_id = user["user_id"]
    offset = (page - 1) * page_size
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Build the WHERE clause dynamically
        where_conditions = ["user_id = $1"]
        params = [user_id]
        param_count = 1
        
        if status:
            param_count += 1
            where_conditions.append(f"status = ${param_count}")
            params.append(status.value)
        
        if issue_type:
            param_count += 1
            where_conditions.append(f"issue_type = ${param_count}")
            params.append(issue_type.value)
        
        where_clause = " AND ".join(where_conditions)
        
        # Get total count
        total_count = await conn.fetchval(
            f"SELECT COUNT(*) FROM help_support WHERE {where_clause}",
            *params
        )
        
        # Get tickets with pagination
        param_count += 1
        params.extend([page_size, offset])
        
        tickets = await conn.fetch(
            f"""
            SELECT 
                support_id, user_id, issue_type, issue, description,
                image_s3_urls, require_call, call_id, transaction_id, status, admin_notes,
                resolved_at, created_at, updated_at
            FROM help_support 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
            """,
            *params
        )
        
        ticket_responses = []
        for ticket in tickets:
            ticket_responses.append(SupportTicketResponse(
                support_id=ticket["support_id"],
                user_id=ticket["user_id"],
                issue_type=IssueTypeEnum(ticket["issue_type"]),
                issue=ticket["issue"],
                description=ticket["description"],
                image_s3_urls=ticket["image_s3_urls"] or [],
                require_call=ticket["require_call"],
                call_id=ticket["call_id"],
                transaction_id=ticket["transaction_id"],
                status=SupportStatusEnum(ticket["status"]),
                admin_notes=ticket["admin_notes"],
                resolved_at=ticket["resolved_at"],
                created_at=ticket["created_at"],
                updated_at=ticket["updated_at"]
            ))
        
        return SupportTicketListResponse(
            tickets=ticket_responses,
            total_count=total_count,
            page=page,
            page_size=page_size
        )


@router.get("/both/support/tickets/{support_id}", response_model=SupportTicketResponse)
async def get_support_ticket(
    support_id: int,
    user=Depends(get_current_user_async)
):
    """
    Get a specific support ticket by ID.
    
    Available to:
    - Active customers (can only view their own tickets)
    - Active and verified listeners (can only view their own tickets)
    """
    user_id = user["user_id"]
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        ticket = await conn.fetchrow(
            """
            SELECT 
                support_id, user_id, issue_type, issue, description,
                image_s3_urls, require_call, call_id, transaction_id, status, admin_notes,
                resolved_at, created_at, updated_at
            FROM help_support 
            WHERE support_id = $1 AND user_id = $2
            """,
            support_id, user_id
        )
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Support ticket not found")
        
        return SupportTicketResponse(
            support_id=ticket["support_id"],
            user_id=ticket["user_id"],
            issue_type=IssueTypeEnum(ticket["issue_type"]),
            issue=ticket["issue"],
            description=ticket["description"],
            image_s3_urls=ticket["image_s3_urls"] or [],
            require_call=ticket["require_call"],
            call_id=ticket["call_id"],
            transaction_id=ticket["transaction_id"],
            status=SupportStatusEnum(ticket["status"]),
            admin_notes=ticket["admin_notes"],
            resolved_at=ticket["resolved_at"],
            created_at=ticket["created_at"],
            updated_at=ticket["updated_at"]
        )


@router.get("/admin/support/tickets", response_model=AdminSupportTicketListResponse)
async def get_all_support_tickets_admin(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of tickets per page"),
    status: Optional[SupportStatusEnum] = Query(None, description="Filter by ticket status"),
    issue_type: Optional[IssueTypeEnum] = Query(None, description="Filter by issue type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    username: Optional[str] = Query(None, description="Filter by username (partial match)"),
    phone: Optional[str] = Query(None, description="Filter by phone number (partial match)"),
    created_from: Optional[str] = Query(None, description="Filter tickets created from date (YYYY-MM-DD)"),
    created_to: Optional[str] = Query(None, description="Filter tickets created to date (YYYY-MM-DD)"),
    require_call: Optional[bool] = Query(None, description="Filter by require_call flag"),
    sort_by: str = Query("created_at", description="Sort by field (created_at, updated_at, support_id)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)")
):
    """
    Get all support tickets for admin with multiple filters.
    
    This endpoint provides comprehensive filtering and sorting options for administrators
    to manage support tickets. No authentication required.
    
    Filters available:
    - status: Filter by ticket status (active, resolved)
    - issue_type: Filter by issue type (call_session_support, payment_support, other)
    - user_id: Filter by specific user ID
    - username: Filter by username (partial match)
    - phone: Filter by phone number (partial match)
    - created_from: Filter tickets created from date
    - created_to: Filter tickets created to date
    - require_call: Filter by require_call flag
    
    Sorting options:
    - sort_by: created_at, updated_at, support_id
    - sort_order: asc, desc
    """
    offset = (page - 1) * page_size
    
    # Validate sort parameters
    valid_sort_fields = ["created_at", "updated_at", "support_id"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"
        )
    
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid sort_order. Must be 'asc' or 'desc'"
        )
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Build the WHERE clause dynamically
        where_conditions = []
        params = []
        param_count = 0
        
        if status:
            param_count += 1
            where_conditions.append(f"hs.status = ${param_count}")
            params.append(status.value)
        
        if issue_type:
            param_count += 1
            where_conditions.append(f"hs.issue_type = ${param_count}")
            params.append(issue_type.value)
        
        if user_id:
            param_count += 1
            where_conditions.append(f"hs.user_id = ${param_count}")
            params.append(user_id)
        
        if username:
            param_count += 1
            where_conditions.append(f"u.username ILIKE ${param_count}")
            params.append(f"%{username}%")
        
        if phone:
            param_count += 1
            where_conditions.append(f"u.phone ILIKE ${param_count}")
            params.append(f"%{phone}%")
        
        if created_from:
            param_count += 1
            where_conditions.append(f"hs.created_at >= ${param_count}::date")
            params.append(created_from)
        
        if created_to:
            param_count += 1
            where_conditions.append(f"hs.created_at <= ${param_count}::date + INTERVAL '1 day'")
            params.append(created_to)
        
        if require_call is not None:
            param_count += 1
            where_conditions.append(f"hs.require_call = ${param_count}")
            params.append(require_call)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Get total count
        total_count = await conn.fetchval(
            f"""
            SELECT COUNT(*) 
            FROM help_support hs
            JOIN users u ON hs.user_id = u.user_id
            WHERE {where_clause}
            """,
            *params
        )
        
        # Get tickets with pagination and sorting
        param_count += 1
        params.extend([page_size, offset])
        
        # Validate sort field to prevent SQL injection
        sort_field = f"hs.{sort_by}" if sort_by in valid_sort_fields else "hs.created_at"
        order_clause = f"ORDER BY {sort_field} {sort_order.upper()}"
        
        tickets = await conn.fetch(
            f"""
            SELECT 
                hs.support_id, hs.user_id, u.username, u.phone,
                hs.issue_type, hs.issue, hs.description,
                hs.image_s3_urls, hs.require_call, hs.call_id, hs.transaction_id,
                hs.status, hs.admin_notes, hs.resolved_at,
                hs.created_at, hs.updated_at
            FROM help_support hs
            JOIN users u ON hs.user_id = u.user_id
            WHERE {where_clause}
            {order_clause}
            LIMIT ${param_count} OFFSET ${param_count + 1}
            """,
            *params
        )
        
        ticket_responses = []
        for ticket in tickets:
            ticket_responses.append(AdminSupportTicketResponse(
                support_id=ticket["support_id"],
                user_id=ticket["user_id"],
                username=ticket["username"],
                phone=ticket["phone"],
                issue_type=IssueTypeEnum(ticket["issue_type"]),
                issue=ticket["issue"],
                description=ticket["description"],
                image_s3_urls=ticket["image_s3_urls"] or [],
                require_call=ticket["require_call"],
                call_id=ticket["call_id"],
                transaction_id=ticket["transaction_id"],
                status=SupportStatusEnum(ticket["status"]),
                admin_notes=ticket["admin_notes"],
                resolved_at=ticket["resolved_at"],
                created_at=ticket["created_at"],
                updated_at=ticket["updated_at"]
            ))
        
        return AdminSupportTicketListResponse(
            tickets=ticket_responses,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
