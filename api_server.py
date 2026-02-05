# Load environment and logging FIRST (before any agent imports)
from core.config import logger  # noqa: F401

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.routes import router, limiter
from core.runners import AGENTS

# Create FastAPI app
app = FastAPI(
    title="Agent API",
    description="REST API for interacting with Google ADK agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routes
app.include_router(router)

# Development server
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
        log_level="info",
    )
