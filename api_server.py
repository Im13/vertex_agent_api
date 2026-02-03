"""
FastAPI Server for Agent API
Provides REST endpoints to interact with all agents via HTTP.
"""

import uuid
import logging
import asyncio
import time as time_module
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("agent_api")

# Load environment variables FIRST before importing agents
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.genai import types as adk_types

# Custom session service that auto-creates sessions
class AutoCreateSessionService(InMemorySessionService):
    """Session service that automatically creates sessions on first access"""

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config=None,
    ):
        """Get or auto-create a session"""
        # Try to get existing session
        existing = await super().get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            config=config
        )

        if existing:
            return existing

        # Session doesn't exist, create it using the parent's structure:
        # self.sessions[app_name][user_id][session_id] = session
        if app_name not in self.sessions:
            self.sessions[app_name] = {}
        if user_id not in self.sessions[app_name]:
            self.sessions[app_name][user_id] = {}

        # Create new session
        import time
        new_session = Session(
            app_name=app_name,
            user_id=user_id,
            id=session_id,
            state={},
            last_update_time=time.time(),
        )

        self.sessions[app_name][user_id][session_id] = new_session
        return new_session

# Import agents (after loading .env)
from agents.basic.agent import root_agent as basic_agent
from agents.company_policy.agent import primary_agent, secondary_agent
from agents.procurement.agent import root_agent as procurement_agent

# Initialize FastAPI app
app = FastAPI(
    title="Agent API",
    description="REST API for interacting with Google ADK agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tạo limiter để bảo vệ API
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Agent registry
AGENTS = {
    "basic": basic_agent,
    "company_policy": primary_agent,  # default for /agents list
    "procurement": procurement_agent,
}

# Create runners for each agent
RUNNERS: Dict[str, Runner] = {}
for agent_name, agent in AGENTS.items():
    RUNNERS[agent_name] = Runner(
        agent=agent,
        app_name=f"{agent_name}_app",
        session_service=AutoCreateSessionService(),
        artifact_service=InMemoryArtifactService()
    )

# Create separate runner for secondary company policy agent
RUNNERS["company_policy_secondary"] = Runner(
    agent=secondary_agent,
    app_name="company_policy_secondary_app",
    session_service=AutoCreateSessionService(),
    artifact_service=InMemoryArtifactService()
)

# Helper function to run an agent and get response with retry
MAX_RETRIES = 3

async def run_agent(runner: Runner, user_id: str, session_id: str, message: str) -> str:
    user_message = adk_types.Content(
        role="user",
        parts=[adk_types.Part(text=message)]
    )

    for attempt in range(MAX_RETRIES):
        try:
            events_async = runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message
            )
            agent_response = "(No response generated)"
            async for event in events_async:
                if event.is_final_response() and event.content and event.content.role == "model":
                    if event.content.parts and event.content.parts[0].text:
                        agent_response = event.content.parts[0].text
            return agent_response

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = (attempt + 1) * 10  # 10s, 20s, 30s
                logger.warning(f"[RETRY] Rate limited (429). Waiting {wait_time}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(wait_time)
            else:
                raise  # Re-raise non-429 errors immediately

    raise Exception("Hệ thống đang quá tải, vui lòng thử lại sau 1 phút.")

# ============================================================================
# Request/Response Models
# ============================================================================

class ChatMessage(BaseModel):
    """A chat message from user or agent"""
    role: str = Field(..., description="Role: 'user' or 'model'")
    content: str = Field(..., description="Message content")

class ChatRequest(BaseModel):
    """Request to chat with an agent"""
    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field(default="default_user", description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")

class ChatResponse(BaseModel):
    """Response from agent"""
    agent: str = Field(..., description="Agent name")
    message: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID")
    timestamp: str = Field(..., description="Response timestamp")

class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    agent: str
    user_id: str
    message_count: int
    created_at: Optional[str] = None

class AgentInfo(BaseModel):
    """Agent information"""
    name: str
    description: str
    model: str
    available: bool

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    agents_available: int

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["General"])
async def root():
    """API root endpoint"""
    return {
        "service": "Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "agents": list(AGENTS.keys())
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        agents_available=len(AGENTS)
    )

@app.get("/agents", response_model=List[AgentInfo], tags=["Agents"])
async def list_agents():
    """List all available agents"""
    agents_info = []
    for name, agent in AGENTS.items():
        agents_info.append(AgentInfo(
            name=name,
            description=agent.description if hasattr(agent, 'description') else "No description",
            model=agent.model if hasattr(agent, 'model') else "unknown",
            available=True
        ))
    return agents_info

@app.post("/public/agents/{agent_name}/chat", response_model=ChatResponse, tags=["Public Chat"])
@limiter.limit("15/minute")
async def public_chat_with_agent(
    request: Request,
    agent_name: str,
    chat_request: ChatRequest = Body(...)
):
    client_ip = get_remote_address(request)
    start_time = time_module.time()

    if agent_name not in AGENTS:
        logger.warning(f"[REQUEST] ip={client_ip} agent={agent_name} - Agent not found")
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    user_id = chat_request.user_id or "anonymous"
    session_id = chat_request.session_id or str(uuid.uuid4())

    logger.info(f"[REQUEST] ip={client_ip} agent={agent_name} user={user_id} session={session_id} message=\"{chat_request.message[:100]}\"")

    try:
        # Company policy: search primary first, fallback to secondary
        if agent_name == "company_policy":
            logger.info(f"[POLICY] Searching primary data store...")
            agent_response = await run_agent(
                RUNNERS["company_policy"], user_id, session_id, chat_request.message
            )

            # If primary didn't find info, try secondary
            if "PRIMARY_NOT_FOUND" in agent_response:
                logger.info(f"[POLICY] Primary not found, searching secondary data store...")
                agent_response = await run_agent(
                    RUNNERS["company_policy_secondary"], user_id, session_id, chat_request.message
                )
        else:
            agent_response = await run_agent(
                RUNNERS[agent_name], user_id, session_id, chat_request.message
            )

        elapsed = round(time_module.time() - start_time, 2)
        logger.info(f"[RESPONSE] ip={client_ip} agent={agent_name} user={user_id} session={session_id} status=200 time={elapsed}s response=\"{agent_response[:100]}\"")

        return ChatResponse(
            agent=agent_name,
            message=agent_response,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        elapsed = round(time_module.time() - start_time, 2)
        logger.error(f"[ERROR] ip={client_ip} agent={agent_name} user={user_id} session={session_id} time={elapsed}s error=\"{str(e)}\"")
        raise HTTPException(
            status_code=500,
            detail=f"Error running agent: {str(e)}"
        )

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print("Agent API Server")
    print("=" * 80)
    print(f"URL: http://localhost:8000")
    print(f"Docs: http://localhost:8000/docs")
    print(f"Available agents: {', '.join(AGENTS.keys())}")
    print("=" * 80)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
