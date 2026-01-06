"""Tracking system for bot generation process."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a generation step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepType(Enum):
    """Type of generation step."""
    PLANNING = "planning"
    BOT_CREATION = "bot_creation"
    STEP_CREATION = "step_creation"
    REQUEST_CREATION = "request_creation"
    CONNECTION_GROUP_CREATION = "connection_group_creation"
    CONNECTION_CREATION = "connection_creation"
    VALIDATION = "validation"
    EXECUTION = "execution"


@dataclass
class GenerationStep:
    """A single step in the bot generation process."""
    id: str = field(default_factory=lambda: str(uuid4()))
    type: StepType = StepType.PLANNING
    name: str = ""
    description: str = ""
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    tool_used: Optional[str] = None
    reasoning: str = ""
    dependencies: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    parent: Optional[str] = None


@dataclass
class GenerationSession:
    """A complete bot generation session."""
    id: str = field(default_factory=lambda: str(uuid4()))
    user_prompt: str = ""
    bot_name: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    status: StepStatus = StepStatus.PENDING
    steps: Dict[str, GenerationStep] = field(default_factory=dict)
    current_step: Optional[str] = None
    root_step: Optional[str] = None
    final_bot_id: Optional[str] = None
    final_bot_data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    reasoning_chain: List[str] = field(default_factory=list)
    tool_usage: Dict[str, int] = field(default_factory=dict)
    total_duration: Optional[float] = None
    events: List[Dict[str, Any]] = field(default_factory=list)


class GenerationTracker:
    """Tracks the bot generation process."""
    
    def __init__(self):
        self.sessions: Dict[str, GenerationSession] = {}
        self.active_sessions: Dict[str, str] = {}  # user_id -> session_id
        self._lock = asyncio.Lock()
    
    async def start_session(
        self, 
        user_prompt: str, 
        bot_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> GenerationSession:
        """Start a new generation session."""
        async with self._lock:
            session = GenerationSession(
                user_prompt=user_prompt,
                bot_name=bot_name
            )
            self.sessions[session.id] = session
            
            if user_id:
                self.active_sessions[user_id] = session.id
            
            logger.info(f"Started generation session {session.id} for prompt: {user_prompt[:100]}...")
            return session
    
    async def add_step(
        self,
        session_id: str,
        step_type: StepType,
        name: str,
        description: str = "",
        parent_step_id: Optional[str] = None,
        tool_used: Optional[str] = None,
        reasoning: str = ""
    ) -> GenerationStep:
        """Add a new step to the session."""
        async with self._lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            step = GenerationStep(
                type=step_type,
                name=name,
                description=description,
                tool_used=tool_used,
                reasoning=reasoning,
                parent=parent_step_id
            )
            
            session.steps[step.id] = step
            session.current_step = step.id
            session.updated_at = time.time()
            
            if parent_step_id and parent_step_id in session.steps:
                session.steps[parent_step_id].children.append(step.id)
                step.dependencies.append(parent_step_id)
            
            if not session.root_step:
                session.root_step = step.id
            
            logger.info(f"Added step {step.id} ({step_type.value}) to session {session_id}")
            return step
    
    async def start_step(self, session_id: str, step_id: str) -> None:
        """Mark a step as started."""
        async with self._lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            if step_id not in session.steps:
                raise ValueError(f"Step {step_id} not found in session {session_id}")
            
            step = session.steps[step_id]
            step.status = StepStatus.IN_PROGRESS
            step.start_time = time.time()
            session.updated_at = time.time()
            
            logger.info(f"Started step {step_id} in session {session_id}")
    
    async def complete_step(
        self,
        session_id: str,
        step_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Mark a step as completed or failed."""
        async with self._lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            if step_id not in session.steps:
                raise ValueError(f"Step {step_id} not found in session {session_id}")
            
            step = session.steps[step_id]
            step.end_time = time.time()
            step.duration = step.end_time - (step.start_time or step.end_time)
            
            if error_message:
                step.status = StepStatus.FAILED
                step.error_message = error_message
                session.errors.append(f"Step {step.name}: {error_message}")
            else:
                step.status = StepStatus.COMPLETED
                if output_data:
                    step.output_data = output_data
            
            session.updated_at = time.time()
            
            # Update tool usage
            if step.tool_used:
                session.tool_usage[step.tool_used] = session.tool_usage.get(step.tool_used, 0) + 1
            
            # Add reasoning to chain
            if step.reasoning:
                session.reasoning_chain.append(f"[{step.type.value}] {step.reasoning}")
            
            logger.info(f"Completed step {step_id} in session {session_id} with status {step.status.value}")
    
    async def update_step_input(self, session_id: str, step_id: str, input_data: Dict[str, Any]) -> None:
        """Update step input data."""
        async with self._lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            if step_id not in session.steps:
                raise ValueError(f"Step {step_id} not found in session {session_id}")
            
            step = session.steps[step_id]
            step.input_data.update(input_data)
            session.updated_at = time.time()
    
    async def get_session(self, session_id: str) -> Optional[GenerationSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    async def get_active_session(self, user_id: str) -> Optional[GenerationSession]:
        """Get the active session for a user."""
        session_id = self.active_sessions.get(user_id)
        if session_id:
            return self.sessions.get(session_id)
        return None
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get detailed status of a session."""
        session = await self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Calculate progress
        total_steps = len(session.steps)
        completed_steps = sum(1 for step in session.steps.values() if step.status == StepStatus.COMPLETED)
        failed_steps = sum(1 for step in session.steps.values() if step.status == StepStatus.FAILED)
        
        # Calculate total duration
        if session.steps:
            start_times = [s.start_time for s in session.steps.values() if s.start_time]
            end_times = [s.end_time for s in session.steps.values() if s.end_time]
            
            if start_times and end_times:
                session.total_duration = max(end_times) - min(start_times)
        
        return {
            "session_id": session_id,
            "status": session.status.value,
            "progress": {
                "total_steps": total_steps,
                "completed": completed_steps,
                "failed": failed_steps,
                "percentage": (completed_steps / total_steps * 100) if total_steps > 0 else 0
            },
            "duration": session.total_duration,
            "current_step": session.current_step,
            "errors": session.errors,
            "warnings": session.warnings,
            "tool_usage": session.tool_usage,
            "reasoning_chain": session.reasoning_chain,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
    
    async def get_session_steps(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all steps in a session with their details."""
        session = await self.get_session(session_id)
        if not session:
            return []
        
        steps_data = []
        for step in session.steps.values():
            steps_data.append({
                "id": step.id,
                "type": step.type.value,
                "name": step.name,
                "description": step.description,
                "status": step.status.value,
                "start_time": step.start_time,
                "end_time": step.end_time,
                "duration": step.duration,
                "tool_used": step.tool_used,
                "reasoning": step.reasoning,
                "error_message": step.error_message,
                "input_data": step.input_data,
                "output_data": step.output_data,
                "dependencies": step.dependencies,
                "children": step.children,
                "parent": step.parent
            })
        
        return steps_data
    
    async def finalize_session(
        self,
        session_id: str,
        bot_id: Optional[str] = None,
        bot_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Finalize a session with the final bot."""
        async with self._lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            session.final_bot_id = bot_id
            session.final_bot_data = bot_data
            session.status = StepStatus.COMPLETED
            session.updated_at = time.time()
            
            logger.info(f"Finalized session {session_id} with bot {bot_id}")

    async def add_event(
        self,
        session_id: str,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a streaming event for the session."""
        async with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                session = GenerationSession(
                    id=session_id,
                    user_prompt="Streaming session",
                    status=StepStatus.IN_PROGRESS,
                )
                self.sessions[session_id] = session
                logger.debug("Created placeholder session %s for tracking events", session_id)
            event: Dict[str, Any] = {
                "id": str(uuid4()),
                "type": event_type,
                "data": data or {},
                "timestamp": time.time(),
            }
            session.events.append(event)
            session.updated_at = time.time()

            if event_type == "ai_thought":
                chunk = event["data"].get("chunk")
                if chunk:
                    session.reasoning_chain.append(chunk)

            return event

    async def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Return streaming events associated with the session."""
        session = await self.get_session(session_id)
        if not session:
            return []
        return list(session.events)

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the session for display."""
        session = await self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        status_info = await self.get_session_status(session_id)
        steps_info = await self.get_session_steps(session_id)
        
        return {
            "session": {
                "id": session_id,
                "user_prompt": session.user_prompt,
                "bot_name": session.bot_name,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "final_bot_id": session.final_bot_id
            },
            "status": status_info,
            "steps": steps_info,
            "summary": {
                "total_steps": len(session.steps),
                "successful_steps": sum(1 for s in session.steps.values() if s.status == StepStatus.COMPLETED),
                "failed_steps": sum(1 for s in session.steps.values() if s.status == StepStatus.FAILED),
                "total_duration": session.total_duration,
                "tools_used": list(session.tool_usage.keys()),
                "reasoning_steps": len(session.reasoning_chain)
            }
        }


# Global tracker instance
tracker = GenerationTracker()

