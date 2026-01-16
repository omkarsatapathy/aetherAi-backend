"""FastAPI application initialization and configuration."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.database import DatabaseManager
from src.config import Config
from src.logging_config import setup_logging
from .routes import chat, sessions, messages, documents, models, voice, setup, image, config, gmail_auth, user_info, feedback, quick_response

# Setup logging
logger = setup_logging(Config.LOG_LEVEL, Config.LOG_TO_FILE, Config.LOG_TO_CONSOLE)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    
    # Initialize FastAPI app
    app = FastAPI(title="Chatbot API")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Inject database manager into route modules
    sessions.set_db_manager(db_manager)
    messages.set_db_manager(db_manager)
    documents.set_db_manager(db_manager)
    
    # Include routers
    app.include_router(chat.router)
    app.include_router(sessions.router)
    app.include_router(messages.router)
    app.include_router(documents.router)
    app.include_router(models.router)
    app.include_router(gmail_auth.router)  # Gmail OAuth routes
    app.include_router(voice.router)
    app.include_router(setup.router)
    app.include_router(image.router)
    app.include_router(config.router)
    app.include_router(user_info.router)
    app.include_router(feedback.router)  # User feedback routes
    app.include_router(quick_response.router)  # Quick response endpoint
    
    logger.info("✅ All routers registered, including quick response router")
    
    # Root endpoint
    @app.get("/")
    async def read_root():
        """Welcome endpoint."""
        return {"message": "Welcome to the AetherAI Backend"}
    
    # Health check endpoint for Cloud Run
    @app.get("/api/health")
    async def health_check():
        """Check API health status (used by Cloud Run health checks)."""
        return {
            "status": "healthy",
            "service": "agentic-chatbot",
            "version": "1.0.0"
        }
    

    # Simple root health check for Cloud Run startup probe
    @app.get("/health")
    async def root_health():
        """Simple health check for Cloud Run."""
        return {"status": "ok"}

    # Debug endpoint to check auth header (no auth required)
    @app.get("/api/debug/auth")
    async def debug_auth(request: Request):
        """Debug endpoint to check what auth header is being sent."""
        auth_header = request.headers.get('Authorization', 'NO AUTH HEADER')
        
        # Don't log the full token for security, just the structure
        if auth_header and auth_header != 'NO AUTH HEADER':
            parts = auth_header.split(' ')
            if len(parts) == 2:
                scheme = parts[0]
                token = parts[1]
                token_preview = f"{token[:20]}...{token[-10:]}" if len(token) > 30 else token
                return {
                    "auth_header_present": True,
                    "scheme": scheme,
                    "token_length": len(token),
                    "token_preview": token_preview,
                    "message": "Token found - check if it's a valid Firebase ID token"
                }
            else:
                return {
                    "auth_header_present": True,
                    "error": "Malformed auth header",
                    "raw_parts_count": len(parts),
                    "message": "Expected format: 'Bearer <token>'"
                }
        return {
            "auth_header_present": False,
            "message": "No Authorization header found. Frontend must send 'Authorization: Bearer <firebase_id_token>'"
        }

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Log when the application starts."""
        logger.info("FastAPI application started and ready to accept requests")
        from src.config import Config
        print(f"Application started successfully on port {Config.FASTAPI_PORT}", flush=True)

    logger.info("FastAPI application initialized successfully")
    return app
