"""API routes for bot generation tracking."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.tracking import tracker, StepStatus, StepType
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tracking", tags=["tracking"])


class StartSessionRequest(BaseModel):
    """Request to start a new generation session."""
    user_prompt: str
    bot_name: Optional[str] = None
    user_id: Optional[str] = None


class AddStepRequest(BaseModel):
    """Request to add a step to a session."""
    session_id: str
    step_type: str
    name: str
    description: str = ""
    parent_step_id: Optional[str] = None
    tool_used: Optional[str] = None
    reasoning: str = ""


class UpdateStepRequest(BaseModel):
    """Request to update a step."""
    session_id: str
    step_id: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class CompleteStepRequest(BaseModel):
    """Request to complete a step."""
    session_id: str
    step_id: str
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class FinalizeSessionRequest(BaseModel):
    """Request to finalize a session."""
    session_id: str
    bot_id: Optional[str] = None
    bot_data: Optional[Dict[str, Any]] = None


class TrackingEventRequest(BaseModel):
    """Arbitrary event pushed from auxiliary services (e.g., MCP) to the tracker."""
    type: str
    data: Optional[Dict[str, Any]] = None


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a WebSocket connection for a session."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_update(self, session_id: str, message: Dict[str, Any]):
        """Send update to all connections for a session."""
        if session_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[session_id].remove(connection)


# Global connection manager
connection_manager = ConnectionManager()


@router.post("/sessions/start")
async def start_session(request: StartSessionRequest) -> Dict[str, Any]:
    """Start a new bot generation session."""
    try:
        session = await tracker.start_session(
            user_prompt=request.user_prompt,
            bot_name=request.bot_name,
            user_id=request.user_id
        )
        
        # Send initial update via WebSocket
        await connection_manager.send_update(session.id, {
            "type": "session_started",
            "session_id": session.id,
            "user_prompt": session.user_prompt,
            "bot_name": session.bot_name,
            "timestamp": session.created_at
        })
        
        return {
            "success": True,
            "session_id": session.id,
            "message": "Session started successfully"
        }
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/steps")
async def add_step(session_id: str, request: AddStepRequest) -> Dict[str, Any]:
    """Add a new step to a session."""
    try:
        step_type = StepType(request.step_type)
        step = await tracker.add_step(
            session_id=session_id,
            step_type=step_type,
            name=request.name,
            description=request.description,
            parent_step_id=request.parent_step_id,
            tool_used=request.tool_used,
            reasoning=request.reasoning
        )
        
        # Send update via WebSocket
        await connection_manager.send_update(session_id, {
            "type": "step_added",
            "step_id": step.id,
            "step_type": step.type.value,
            "name": step.name,
            "description": step.description,
            "tool_used": step.tool_used,
            "reasoning": step.reasoning,
            "timestamp": step.start_time or 0
        })
        
        return {
            "success": True,
            "step_id": step.id,
            "message": "Step added successfully"
        }
    except Exception as e:
        logger.error(f"Error adding step: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/steps/{step_id}/start")
async def start_step(session_id: str, step_id: str) -> Dict[str, Any]:
    """Start a step execution."""
    try:
        await tracker.start_step(session_id, step_id)
        
        # Send update via WebSocket
        await connection_manager.send_update(session_id, {
            "type": "step_started",
            "step_id": step_id,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        return {"success": True, "message": "Step started"}
    except Exception as e:
        logger.error(f"Error starting step: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/steps/{step_id}/complete")
async def complete_step(session_id: str, step_id: str, request: CompleteStepRequest) -> Dict[str, Any]:
    """Complete a step execution."""
    try:
        await tracker.complete_step(
            session_id=session_id,
            step_id=step_id,
            output_data=request.output_data,
            error_message=request.error_message
        )
        
        # Get updated step info
        session = await tracker.get_session(session_id)
        step = session.steps[step_id] if session else None
        
        # Send update via WebSocket
        await connection_manager.send_update(session_id, {
            "type": "step_completed",
            "step_id": step_id,
            "status": step.status.value if step else "unknown",
            "duration": step.duration if step else None,
            "error_message": step.error_message if step else None,
            "timestamp": step.end_time if step else 0
        })
        
        return {"success": True, "message": "Step completed"}
    except Exception as e:
        logger.error(f"Error completing step: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/finalize")
async def finalize_session(session_id: str, request: FinalizeSessionRequest) -> Dict[str, Any]:
    """Finalize a session with the final bot."""
    try:
        await tracker.finalize_session(
            session_id=session_id,
            bot_id=request.bot_id,
            bot_data=request.bot_data
        )
        
        # Send final update via WebSocket
        await connection_manager.send_update(session_id, {
            "type": "session_finalized",
            "session_id": session_id,
            "bot_id": request.bot_id,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        return {"success": True, "message": "Session finalized"}
    except Exception as e:
        logger.error(f"Error finalizing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """Get session information."""
    try:
        session = await tracker.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "session": {
                "id": session.id,
                "user_prompt": session.user_prompt,
                "bot_name": session.bot_name,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "final_bot_id": session.final_bot_id
            }
        }
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str) -> Dict[str, Any]:
    """Get detailed session status."""
    try:
        status = await tracker.get_session_status(session_id)
        return {"success": True, "status": status}
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/steps")
async def get_session_steps(session_id: str) -> Dict[str, Any]:
    """Get all steps in a session."""
    try:
        steps = await tracker.get_session_steps(session_id)
        return {"success": True, "steps": steps}
    except Exception as e:
        logger.error(f"Error getting session steps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str) -> Dict[str, Any]:
    """Get a complete session summary."""
    try:
        summary = await tracker.get_session_summary(session_id)
        return {"success": True, "summary": summary}
    except Exception as e:
        logger.error(f"Error getting session summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/events")
async def push_session_event(
    session_id: str,
    request: Request,
    event: TrackingEventRequest,
) -> Dict[str, Any]:
    """Receive streaming events (e.g. thoughts/tool updates) for a session."""
    try:
        internal_token = request.headers.get("X-Internal-Token")
        service_token = settings.MCP_SERVICE_TOKEN
        if service_token:
            if not internal_token or internal_token != service_token:
                raise HTTPException(status_code=401, detail="Unauthorized")

        stored_event = await tracker.add_event(session_id, event.type, event.data)

        # Broadcast event to subscribed clients
        await connection_manager.send_update(
            session_id,
            {
                "type": "tracking_event",
                "session_id": session_id,
                "event": stored_event,
            },
        )

        return {"success": True, "event": stored_event}
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Failed to record tracking event for session %s: %s", session_id, exc)
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error while recording tracking event: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to record tracking event")


@router.get("/sessions/{session_id}/events")
async def get_session_events(session_id: str) -> Dict[str, Any]:
    """Return all streaming events accumulated for the session."""
    try:
        events = await tracker.get_session_events(session_id)
        if not events:
            # verify session exists by attempting to fetch - tracker returns [] for missing
            session = await tracker.get_session(session_id)
            if session is None:
                raise HTTPException(status_code=404, detail="Session not found")
        return {"success": True, "events": events}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error fetching session events for %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch session events")


@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates."""
    await connection_manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket, session_id)


@router.post("/sessions/{session_id}/apply")
async def apply_changes(session_id: str) -> Dict[str, Any]:
    """Apply changes from a session."""
    try:
        # This would implement the logic to apply changes
        # For now, just return success
        return {"success": True, "message": "Changes applied successfully"}
    except Exception as e:
        logger.error(f"Error applying changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/rollback")
async def rollback_changes(session_id: str) -> Dict[str, Any]:
    """Rollback changes from a session."""
    try:
        # This would implement the logic to rollback changes
        # For now, just return success
        return {"success": True, "message": "Changes rolled back successfully"}
    except Exception as e:
        logger.error(f"Error rolling back changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """List all sessions."""
    try:
        # This would need to be implemented in the tracker
        # For now, return empty list
        return {"success": True, "sessions": [], "count": 0}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
