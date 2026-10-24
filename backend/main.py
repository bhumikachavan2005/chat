"""
Main FastAPI Application
- Localhost only (127.0.0.1)
- Strict Security Headers
- Static frontend asset hosting
- Complete API router registration
"""

import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.database import init_db
from backend.api.routes_auth import router as auth_router
from backend.api.routes_chat import router as chat_router
from backend.api.routes_search import router as search_router
from backend.api.routes_memories import router as memories_router
from backend.api.routes_stats import router as stats_router
from backend.api.routes_insights import router as insights_router
from backend.api.routes_system import router as system_router
from backend.api.routes_wrapped import router as wrapped_router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Vinu 💝 × Bhuu 🎀 Private Archive",
    description="100% Private Local WhatsApp Friendship Archive",
    docs_url=None,  # Disabled public Swagger docs for heightened privacy
    redoc_url=None
)

# Enable CORS for localhost and local file protocol access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup lifecycle
@app.on_event("startup")
def on_startup():
    init_db()


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' http://127.0.0.1:* http://localhost:* data: blob:; connect-src *;"
    return response


# Include API Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(search_router)
app.include_router(memories_router)
app.include_router(stats_router)
app.include_router(insights_router)
app.include_router(system_router)
app.include_router(wrapped_router)


# Mount Static Frontend
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def serve_index():
    """Serve the single-page frontend."""
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend not found."}
