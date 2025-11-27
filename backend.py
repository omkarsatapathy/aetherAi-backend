"""FastAPI backend for the chatbot application - Main entry point."""
import sys
import warnings
from pathlib import Path

# Suppress OpenTelemetry context detach warnings (known issue with async context management)
warnings.filterwarnings("ignore", message=".*Failed to detach context.*")
warnings.filterwarnings("ignore", message=".*was created in a different Context.*")

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.api import create_app
from src.config import Config
from src.api.routes.image_routes import router as image_router  # Import image router
from src.api.routes.test_endpoint import router as test_router  # Import test router
from src.api.routes.chat_simple import router as chat_simple_router  # Import chat_simple router

# Create the FastAPI application
app = create_app()

# Register the image router
app.include_router(image_router)
app.include_router(test_router)  # Register the test router
app.include_router(chat_simple_router)  # Register the chat_simple router


if __name__ == "__main__":
    import uvicorn
    host, port = Config.get_server_config()
    uvicorn.run(
        "backend:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=[".", "src", "frontend"],
        log_level="warning"  # Reduce log verbosity (only warnings and errors)
    )
