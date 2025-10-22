from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import json
from api.clients.db import get_db_pool


router = APIRouter(tags=["Realtime"])


# In-memory registry of connected websocket clients
connected_clients: Set[WebSocket] = set()


@router.websocket("/ws/verification")
async def websocket_verification(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)

    try:
        while True:
            # Receive event from a producer/client
            message_text = await websocket.receive_text()
            try:
                event = json.loads(message_text)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON payload"
                }))
                continue

            # Expected event schema
            # {
            #   "listener_id": 123,
            #   "verification_status": true,
            #   "verification_message": "Approved"
            # }

            listener_id = event.get("listener_id")
            verification_status = event.get("verification_status")
            verification_message = event.get("verification_message")

            if listener_id is None or verification_status is None:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Fields 'listener_id' and 'verification_status' are required"
                }))
                continue

            # Only allow transition False -> True. Reject attempts to set False.
            if verification_status is not True:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Only approval is allowed (False -> True). Rejections are not permitted via this socket."
                }))
                continue

            # Persist to DB
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Check current status
                current_row = await conn.fetchrow(
                    """
                    SELECT verification_status, verified_on
                    FROM listener_profile
                    WHERE listener_id = $1
                    """,
                    listener_id,
                )

                if not current_row:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Listener profile not found"
                    }))
                    continue

                already_verified = bool(current_row["verification_status"]) if current_row else False

                if already_verified:
                    # Already verified: optionally update message, do not touch verified_on
                    await conn.execute(
                        """
                        UPDATE listener_profile
                        SET verification_message = COALESCE($2, verification_message),
                            updated_at = NOW()
                        WHERE listener_id = $1
                        """,
                        listener_id,
                        verification_message,
                    )
                else:
                    # Transition from False -> True
                    await conn.execute(
                        """
                        UPDATE listener_profile
                        SET verification_status = TRUE,
                            verification_message = COALESCE($2, verification_message),
                            verified_on = NOW(),
                            updated_at = NOW()
                        WHERE listener_id = $1
                        """,
                        listener_id,
                        verification_message,
                    )

            # Broadcast to all connected clients
            broadcast_payload = json.dumps({
                "type": "verification_update",
                "listener_id": listener_id,
                "verification_status": verification_status,
                "verification_message": verification_message,
            })

            stale_clients: Set[WebSocket] = set()
            for client in connected_clients:
                try:
                    await client.send_text(broadcast_payload)
                except RuntimeError:
                    # Connection likely closed unexpectedly; mark for cleanup
                    stale_clients.add(client)

            # Cleanup closed clients
            for client in stale_clients:
                connected_clients.discard(client)

    except WebSocketDisconnect:
        connected_clients.discard(websocket)


