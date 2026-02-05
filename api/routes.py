"""
API endpoint handlers.
"""

import uuid
import time as time_module
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Body, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import logger
from core.runners import AGENTS, RUNNERS, run_agent, orchestrate_company_policy
from api.models import ChatResponse, ChatRequest, AgentInfo, HealthResponse

router = APIRouter()

# Rate limiter (will be attached to app.state in api_server.py)
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

@router.get("/", tags=["General"])
async def root():
    """API root endpoint."""
    return {
        "service": "Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "agents": list(AGENTS.keys()),
    }


@router.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        agents_available=len(AGENTS),
    )


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

@router.get("/agents", response_model=List[AgentInfo], tags=["Agents"])
async def list_agents():
    """List all available agents."""
    return [
        AgentInfo(
            name=name,
            description=getattr(agent, "description", "No description"),
            model=getattr(agent, "model", "unknown"),
            available=True,
        )
        for name, agent in AGENTS.items()
    ]


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@router.post("/public/agents/{agent_name}/chat", response_model=ChatResponse, tags=["Public Chat"])
@limiter.limit("15/minute")
async def public_chat_with_agent(
    request: Request,
    agent_name: str,
    chat_request: ChatRequest = Body(...),
):
    """Chat with an agent (rate-limited, public endpoint)."""
    client_ip = get_remote_address(request)
    start_time = time_module.time()

    if agent_name not in AGENTS:
        logger.warning(f"[REQUEST] ip={client_ip} agent={agent_name} - Agent not found")
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    user_id = chat_request.user_id or "anonymous"
    session_id = chat_request.session_id or str(uuid.uuid4())

    logger.info(
        f'[REQUEST] ip={client_ip} agent={agent_name} user={user_id} '
        f'session={session_id} message="{chat_request.message[:100]}"'
    )

    try:
        if agent_name == "company_policy":
            agent_response = await orchestrate_company_policy(
                user_id, session_id, chat_request.message
            )
        else:
            agent_response = await run_agent(
                RUNNERS[agent_name], user_id, session_id, chat_request.message
            )

        elapsed = round(time_module.time() - start_time, 2)
        logger.info(
            f'[RESPONSE] ip={client_ip} agent={agent_name} user={user_id} '
            f'session={session_id} status=200 time={elapsed}s '
            f'response="{agent_response[:100]}"'
        )

        return ChatResponse(
            agent=agent_name,
            message=agent_response,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        elapsed = round(time_module.time() - start_time, 2)
        logger.error(
            f'[ERROR] ip={client_ip} agent={agent_name} user={user_id} '
            f'session={session_id} time={elapsed}s error="{str(e)}"'
        )
        raise HTTPException(status_code=500, detail=f"Error running agent: {str(e)}")
