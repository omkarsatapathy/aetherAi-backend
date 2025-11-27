"""Image analysis API routes."""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from ...tools.image_analysis import process_image_message, analyze_image
from ...logging_config import get_logger

logger = get_logger("chatbot.api.image_routes")

router = APIRouter(prefix="/api/image", tags=["Image Analysis"])


class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis."""
    image_base64: str
    question: Optional[str] = None


class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis."""
    success: bool
    result: str
    error: Optional[str] = None


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image_endpoint(request: ImageAnalysisRequest = Body(...)):
    """
    POST endpoint to analyze an image.
    
    Args:
        request: ImageAnalysisRequest with base64 image and optional question
        
    Returns:
        ImageAnalysisResponse with analysis result
        
    Example:
        POST http://localhost:8000/api/image/analyze
        Body: {
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
            "question": "What's in this image?"
        }
    """
    try:
        logger.info("Received image analysis request")
        
        # Process the image
        result = process_image_message(
            image_base64=request.image_base64,
            user_message=request.question or ""
        )
        
        logger.info("Image analysis completed successfully")
        
        return ImageAnalysisResponse(
            success=True,
            result=result,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Image analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image analysis failed: {str(e)}"
        )


@router.post("/analyze-tool", response_model=ImageAnalysisResponse)
async def analyze_image_tool_endpoint(
    image_base64: str = Body(..., embed=True),
    question: Optional[str] = Body(None, embed=True)
):
    """
    Alternative POST endpoint using the @tool decorated function.
    
    Args:
        image_base64: Base64 encoded image data
        question: Optional question about the image
        
    Returns:
        ImageAnalysisResponse with analysis result
        
    Example:
        POST http://localhost:8000/api/image/analyze-tool
        Body: {
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
            "question": "Describe this image"
        }
    """
    try:
        logger.info("Received image analysis request (tool endpoint)")
        
        # Use the @tool decorated function
        result = analyze_image(
            image_base64=image_base64,
            question=question
        )
        
        logger.info("Image analysis completed successfully")
        
        return ImageAnalysisResponse(
            success=True,
            result=result,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Image analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image analysis failed: {str(e)}"
        )
