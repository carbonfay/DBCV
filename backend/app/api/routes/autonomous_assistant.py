"""API routes for autonomous GPT assistant with MCP tools."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.api.dependencies.auth import CurrentDeveloperDep, AnyTokenDep
from app.api.dependencies.db import SessionDep
from app.tracking import tracker

logger = logging.getLogger(__name__)

router = APIRouter()


PLAN_SYSTEM_PROMPT = """
Ты — помощник, который проектирует сценарий DBCV. Тебе нужно составить план действий, но не выполнять их.
Ответ верни строго в формате JSON:
{
  "steps": [
    {"name": "...", "action": "...", "required_data": [], "notes": ""}
  ],
  "missing_data": [],
  "prompt_suggestion": ""
}
Если каких-то полей нет, используй пустые строки или массивы. Никакого текста вне JSON.
"""


def _extract_json_block(text: str) -> Optional[str]:
    """Extract JSON object from model output."""
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return None


class AutonomousPromptIn(BaseModel):
    """Input schema for autonomous assistant prompt."""
    prompt: str = Field(..., min_length=1, description="Natural language prompt for bot creation/modification")
    bot_id: Optional[str] = Field(None, description="Bot ID to modify (if None, creates new bot)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the assistant")
    session_id: Optional[str] = Field(None, description="Tracking session ID")


class AutonomousResponseOut(BaseModel):
    """Output schema for autonomous assistant response."""
    success: bool = Field(..., description="Whether the operation was successful")
    response_id: Optional[str] = Field(None, description="OpenAI response ID")
    output_text: str = Field(..., description="Assistant's response text")
    tool_calls: list = Field(default_factory=list, description="List of executed tool calls")
    session_id: Optional[str] = Field(None, description="Tracking session ID")
    error: Optional[str] = Field(None, description="Error message if failed")


class PlanStep(BaseModel):
    """Single step of the planning preview."""
    name: str = Field(..., description="Название шага или действия")
    action: str = Field(..., description="Что нужно сделать на шаге")
    required_data: List[str] = Field(default_factory=list, description="Какие данные или переменные требуются")
    notes: Optional[str] = Field(None, description="Дополнительные пояснения")


class AutonomousPlanIn(BaseModel):
    """Input schema for planning preview request."""
    prompt: str = Field(..., min_length=1, description="Задача, которую нужно спланировать")
    bot_id: Optional[str] = Field(None, description="ID бота, если уже существует")
    context: Optional[Dict[str, Any]] = Field(None, description="Дополнительный контекст (переменные, окружение)")


class AutonomousPlanOut(BaseModel):
    """Output schema for planning preview response."""
    steps: List[PlanStep] = Field(default_factory=list, description="Предлагаемая последовательность действий")
    missing_data: List[str] = Field(default_factory=list, description="Значения, которые желательно уточнить")
    prompt_suggestion: Optional[str] = Field(None, description="Рекомендуемый промпт для основного запуска MCP")


class AutonomousAssistantService:
    """Service for autonomous GPT assistant with MCP tools."""
    
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self._assistant = None

    def _enhance_prompt(
        self,
        prompt: str,
        bot_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Attach structured context to the prompt before sending to MCP."""
        parts: list[str] = [prompt.strip()]
        if bot_id:
            parts.append(f"\n[bot_id]: {bot_id}")
        if context:
            try:
                context_json = json.dumps(context, ensure_ascii=False)
                parts.append(f"\n[context]: {context_json}")
            except (TypeError, ValueError):
                parts.append(f"\n[context]: {context}")
        return "\n".join(parts)
    
    async def call_mcp_server(
        self,
        prompt: str,
        *,
        bot_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call MCP server via HTTP API."""
        try:
            import httpx
            import os
            
            mcp_server_url = "https://mcp.platform.eni7.ru"
            
            payload: Dict[str, Any] = {"prompt": prompt}
            if bot_id:
                payload["bot_id"] = bot_id
            if context:
                payload["context"] = context
            if session_id:
                payload["session_id"] = session_id
                payload["stream"] = True
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{mcp_server_url}/mcp/process",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.auth_token}",
                    },
                )

                if response.status_code == 200:
                    return response.json()

                logger.error("MCP server error: %s - %s", response.status_code, response.text)
                return {
                    "success": False,
                    "error": f"MCP server error: {response.status_code}",
                    "output_text": f"Failed to process with MCP server: {response.text}",
                }

        except Exception as exc:
            logger.error("Failed to call MCP server: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "output_text": f"Failed to call MCP server: {exc}",
            }
    
    async def process_prompt(
        self,
        prompt: str,
        bot_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process prompt with autonomous assistant via MCP server."""
        try:
            session_key = session_id or str(uuid.uuid4())
            enhanced_prompt = self._enhance_prompt(prompt, bot_id, context)

            result = await self.call_mcp_server(
                enhanced_prompt,
                bot_id=bot_id,
                context=context,
                session_id=session_key,
            )

            result["session_id"] = session_key
            return result

        except Exception as exc:
            logger.error(f"Autonomous assistant processing failed: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "output_text": f"Failed to process prompt: {exc}",
                "tool_calls": [],
            }

def _build_openai_client(api_key: str) -> AsyncOpenAI:
    proxy = os.getenv("PROXY")
    if proxy and "://" not in proxy:
        proxy = f"http://{proxy}"
    http_client = (
        httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(proxy=proxy))
        if proxy
        else None
    )
    return AsyncOpenAI(api_key=api_key, http_client=http_client)


async def generate_plan_preview(prompt: str, bot_id: Optional[str], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a planning preview using a lightweight model (no MCP calls)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    client = _build_openai_client(api_key)

    user_parts = [f"Задача пользователя: {prompt.strip()}"]
    if bot_id:
        user_parts.append(f"ID бота: {bot_id}")
    if context:
        context_json = json.dumps(context, ensure_ascii=False, indent=2)
        user_parts.append(f"Контекст:\n{context_json}")
    user_input = "\n\n".join(user_parts)

    response = await client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
    )

    output_text = (response.output_text or "").strip()
    json_text = _extract_json_block(output_text)
    if not json_text:
        raise ValueError("Не удалось распознать JSON с планом")

    plan_data = json.loads(json_text)
    plan_data.setdefault("steps", [])
    plan_data.setdefault("missing_data", [])
    plan_data.setdefault("prompt_suggestion", None)
    return plan_data
    
    def _enhance_prompt(self, prompt: str, bot_id: Optional[str], context: Optional[Dict[str, Any]]) -> str:
        """Enhance prompt with additional context."""
        enhanced = prompt
        
        if bot_id:
            enhanced += f"\n\nBot ID: {bot_id}"
        
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            enhanced += f"\n\nAdditional context:\n{context_str}"
        
        return enhanced


@router.post("/plan", response_model=AutonomousPlanOut)
async def generate_autonomous_plan(
    data: AutonomousPlanIn,
    current_user: CurrentDeveloperDep,
) -> AutonomousPlanOut:
    """
    Быстрый предпросмотр плана без запуска MCP. Использует недорогую модель.
    """
    try:
        plan = await generate_plan_preview(
            prompt=data.prompt,
            bot_id=data.bot_id,
            context=data.context,
        )
        return AutonomousPlanOut.model_validate(plan)
    except ValueError as e:
        logger.error(f"Plan preview input error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Plan preview failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plan generation failed: {str(e)}",
        )


@router.post("/generate", response_model=AutonomousResponseOut)
async def generate_with_autonomous_assistant(
    request: Request,
    data: AutonomousPromptIn,
    session: SessionDep,
    current_user: CurrentDeveloperDep,
    jwt_token: AnyTokenDep,
) -> AutonomousResponseOut:
    """
    Generate or modify bot using autonomous GPT assistant with MCP tools.
    
    This endpoint allows developers to use natural language prompts to create
    or modify bots. The assistant will autonomously plan and execute the necessary
    actions using MCP tools.
    
    **Security**: Only users with DEVELOPER role or higher can access this endpoint.
    """
    try:
        # Prepare tracking session
        if not data.session_id:
            tracking_session = await tracker.start_session(
                user_prompt=data.prompt,
                bot_name=f"Bot {data.bot_id}" if data.bot_id else "Generated Bot",
                user_id=current_user.id
            )
            session_id = tracking_session.id
        else:
            session_id = data.session_id
        
        logger.info(f"Autonomous assistant request from user {current_user.id}: {data.prompt[:100]}...")
        
        # Use the real JWT token from the request
        auth_token = jwt_token
        logger.info(f"Using JWT token for MCP authentication: {jwt_token[:20]}...")
        
        service = AutonomousAssistantService(auth_token)
        
        # Process the prompt
        result = await service.process_prompt(
            prompt=data.prompt,
            bot_id=data.bot_id,
            context=data.context,
            session_id=session_id
        )
        
        # Add session ID to result
        result['session_id'] = session_id
        
        # Log the result
        if result.get('success'):
            logger.info(f"Autonomous assistant completed successfully: {len(result.get('tool_calls', []))} tool calls executed")
        else:
            logger.error(f"Autonomous assistant failed: {result.get('error')}")
        
        return AutonomousResponseOut.model_validate(result)
        
    except Exception as e:
        logger.error(f"Autonomous assistant endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Autonomous assistant processing failed: {str(e)}"
        )


@router.get("/status")
async def get_autonomous_assistant_status(
    current_user: CurrentDeveloperDep,
) -> Dict[str, Any]:
    """
    Get status of autonomous assistant service.
    
    **Security**: Only users with DEVELOPER role or higher can access this endpoint.
    """
    try:
        # Check if MCP server is accessible
        import aiohttp
        import os
        
        mcp_server_url = os.getenv("MCP_SERVER_URL", "localhost:8005")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"http://{mcp_server_url}/health", timeout=5) as response:
                    mcp_server_status = "healthy" if response.status == 200 else "unhealthy"
            except Exception:
                mcp_server_status = "unreachable"
        
        # Check OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_status = "configured" if openai_api_key else "not_configured"
        
        return {
            "status": "operational",
            "mcp_server": {
                "url": mcp_server_url,
                "status": mcp_server_status
            },
            "openai": {
                "status": openai_status
            },
            "user": {
                "id": str(current_user.id),
                "role": current_user.role.value
            }
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/test")
async def test_autonomous_assistant(
    current_user: CurrentDeveloperDep,
) -> Dict[str, Any]:
    """
    Test autonomous assistant with a simple prompt.
    
    **Security**: Only users with DEVELOPER role or higher can access this endpoint.
    """
    try:
        # Simple test prompt
        test_prompt = "Создай простого бота для приветствия пользователей с шагом 'Приветствие'"
        
        auth_token = f"user_{current_user.id}_test"
        service = AutonomousAssistantService(auth_token)
        
        result = await service.process_prompt(test_prompt)
        
        return {
            "test_completed": True,
            "result": result,
            "user_id": str(current_user.id)
        }
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {
            "test_completed": False,
            "error": str(e),
            "user_id": str(current_user.id)
        }
