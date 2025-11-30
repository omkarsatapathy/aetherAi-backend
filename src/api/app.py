"""FastAPI application initialization and configuration."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.database import DatabaseManager
from src.config import Config
from src.logging_config import setup_logging
from .routes import chat, sessions, messages, documents, models, voice, setup, image, config
from ..gmail import routes as gmail_routes

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
    app.include_router(gmail_routes.router)  # Updated to use new secure Gmail routes
    app.include_router(voice.router)
    app.include_router(setup.router)
    app.include_router(image.router)
    app.include_router(config.router)
    
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

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Log when the application starts."""
        logger.info("FastAPI application started and ready to accept requests")
        print("Application started successfully on port 8080", flush=True)

    logger.info("FastAPI application initialized successfully")
    return app
