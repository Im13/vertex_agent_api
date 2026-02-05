import asyncio
from typing import Dict

from google.adk.runners import Runner
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.genai import types as adk_types

from core.config import logger
from core.sessions import AutoCreateSessionService

# ---------------------------------------------------------------------------
# Import agents (env vars already loaded by core.config)
# ---------------------------------------------------------------------------
from agents.basic.agent import root_agent as basic_agent
from agents.company_policy.agent import primary_agent, secondary_agent
from agents.procurement.agent import root_agent as procurement_agent

# ---------------------------------------------------------------------------
# Agent registry
# ---------------------------------------------------------------------------
AGENTS = {
    "basic": basic_agent,
    "company_policy": primary_agent,
    "procurement": procurement_agent,
}

# ---------------------------------------------------------------------------
# Create runners for each agent
# ---------------------------------------------------------------------------
RUNNERS: Dict[str, Runner] = {}
for _name, _agent in AGENTS.items():
    RUNNERS[_name] = Runner(
        agent=_agent,
        app_name=f"{_name}_app",
        session_service=AutoCreateSessionService(),
        artifact_service=InMemoryArtifactService(),
    )

# Separate runner for secondary company policy agent
RUNNERS["company_policy_secondary"] = Runner(
    agent=secondary_agent,
    app_name="company_policy_secondary_app",
    session_service=AutoCreateSessionService(),
    artifact_service=InMemoryArtifactService(),
)

# ---------------------------------------------------------------------------
# Execution helpers
# ---------------------------------------------------------------------------
MAX_RETRIES = 3


async def run_agent(runner: Runner, user_id: str, session_id: str, message: str) -> str:
    """Run an agent and return its text response, with retry on 429 errors."""
    user_message = adk_types.Content(
        role="user",
        parts=[adk_types.Part(text=message)],
    )

    for attempt in range(MAX_RETRIES):
        try:
            events_async = runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message,
            )
            agent_response = "(No response generated)"
            async for event in events_async:
                if (
                    event.is_final_response()
                    and event.content
                    and event.content.role == "model"
                ):
                    if event.content.parts and event.content.parts[0].text:
                        agent_response = event.content.parts[0].text
            return agent_response

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = (attempt + 1) * 10  # 10s, 20s, 30s
                logger.warning(
                    f"[RETRY] Rate limited (429). Waiting {wait_time}s... "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(wait_time)
            else:
                raise

    raise Exception("Hệ thống đang quá tải, vui lòng thử lại sau 1 phút.")


async def orchestrate_company_policy(user_id: str, session_id: str, message: str) -> str:
    """Company policy: search primary data store first, fallback to secondary."""
    logger.info("[POLICY] Searching primary data store...")
    response = await run_agent(RUNNERS["company_policy"], user_id, session_id, message)

    if "PRIMARY_NOT_FOUND" in response:
        logger.info("[POLICY] Primary not found, searching secondary data store...")
        response = await run_agent(
            RUNNERS["company_policy_secondary"], user_id, session_id, message
        )

    return response
