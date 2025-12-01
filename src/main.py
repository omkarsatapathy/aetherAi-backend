"""Main application entry point."""
from src.api.app import create_app

# Create the FastAPI app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    from src.config import Config
    uvicorn.run(app, host="0.0.0.0", port=Config.FASTAPI_PORT)
