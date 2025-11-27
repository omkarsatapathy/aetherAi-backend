"""FastAPI backend for the chatbot application - Main entry point."""
import sys
import os
import warnings
from pathlib import Path

# Print startup info for Cloud Run logs
print("Starting application...", flush=True)
print(f"Python version: {sys.version}", flush=True)
print(f"PORT environment variable: {os.getenv('PORT', 'not set')}", flush=True)

# Suppress OpenTelemetry context detach warnings (known issue with async context management)
warnings.filterwarnings("ignore", message=".*Failed to detach context.*")
warnings.filterwarnings("ignore", message=".*was created in a different Context.*")

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

print("Importing FastAPI app...", flush=True)
from src.api import create_app
from src.config import Config
from src.api.routes.image_routes import router as image_router  # Import image router
from src.api.routes.test_endpoint import router as test_router  # Import test router
from src.api.routes.chat_simple import router as chat_simple_router  # Import chat_simple router

print("Creating FastAPI application...", flush=True)
# Create the FastAPI application
app = create_app()
print("FastAPI application created", flush=True)

# Register the image router
try:
    app.include_router(image_router)
    print("Image router registered", flush=True)
except Exception as e:
    print(f"Warning: Could not register image router: {e}", flush=True)

try:
    app.include_router(test_router)  # Register the test router
    print("Test router registered", flush=True)
except Exception as e:
    print(f"Warning: Could not register test router: {e}", flush=True)

try:
    app.include_router(chat_simple_router)  # Register the chat_simple router
    print("Chat simple router registered", flush=True)
except Exception as e:
    print(f"Warning: Could not register chat_simple router: {e}", flush=True)


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
