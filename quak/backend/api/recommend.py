"""
Recipe recommendation API endpoints.
"""
import time
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

try:
    # Try relative imports first (when run as module)
    from .models import (
        RecommendationRequest, 
        RecommendationResponse, 
        RecipeResult,
        ErrorResponse
    )
    from ..core.config import settings
except ImportError:
    # Fall back to absolute imports (when run directly)
    from api.models import (
        RecommendationRequest, 
        RecommendationResponse, 
        RecipeResult,
        ErrorResponse
    )
    from core.config import settings

router = APIRouter(tags=["recommendations"])


# Dependency to get recommendation service
async def get_recommendation_service():
    """Dependency to get the recommendation service."""
    try:
        from ..core.model_manager import model_manager
        return model_manager.get_recommender()
    except ImportError:
        from core.model_manager import model_manager
        return model_manager.get_recommender()


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get recipe recommendations",
    description="Get recipe recommendations based on available ingredients with optional filters"
)
async def recommend_recipes(
    request: RecommendationRequest,
    service = Depends(get_recommendation_service)
) -> RecommendationResponse:
    """
    Get recipe recommendations based on available ingredients.
    
    Args:
        request: The recommendation request with ingredients and filters
        service: The recommendation service dependency
        
    Returns:
        RecommendationResponse with recommended recipes
        
    Raises:
        HTTPException: If the request is invalid or processing fails
    """
    start_time = time.time()
    
    try:
        # Validate request
        if not request.ingredients:
            raise HTTPException(
                status_code=400,
                detail="At least one ingredient is required"
            )
        
        if len(request.ingredients) > settings.max_ingredients:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {settings.max_ingredients} ingredients allowed"
            )
        
        # Get recommendations from the hybrid recommender
        if service is None:
            raise HTTPException(
                status_code=503,
                detail="Recommendation service not available. Models may not be loaded."
            )
        
        # Get recommendations
        recommendations = service.get_recommendations(
            ingredients=request.ingredients,
            cuisine_filter=request.cuisine_filter,
            diet_filter=request.diet_filter,
            max_results=request.max_results
        )
        
        # Convert to API response format
        recipe_results = []
        for rec in recommendations:
            ingredients_raw = rec.get('ingredients', [])
            if isinstance(ingredients_raw, str):
                ingredients_list = [i.strip() for i in ingredients_raw.split(',') if i.strip()]
            else:
                ingredients_list = list(ingredients_raw)
                
            recipe_result = RecipeResult(
                id=rec.get('recipe_id', 0),
                title=rec.get('title', 'Unknown Recipe'),
                ingredients=ingredients_list,
                cuisine=rec.get('cuisine'),
                diet=rec.get('diet_types'),
                cooking_time=rec.get('cooking_time'),
                difficulty=rec.get('difficulty'),
                match_score=rec.get('match_score', 0.0),
                tfidf_score=rec.get('tfidf_score'),
                embedding_score=rec.get('embedding_score')
            )
            recipe_results.append(recipe_result)
        
        processing_time = time.time() - start_time
        
        # Get model info
        model_info = service.get_model_info() if service else {}
        
        return RecommendationResponse(
            recipes=recipe_results,
            total_found=len(recipe_results),
            processing_time=processing_time,
            model_info=model_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/recommend/filters",
    summary="Get available filter options",
    description="Get available cuisine and diet filter options"
)
async def get_filter_options():
    """
    Get available filter options for cuisine and diet types.
    
    Returns:
        Dictionary with available filter options
    """
    try:
        # Import here to avoid circular imports
        try:
            from ..utils.filters import RecipeFilter
        except ImportError:
            from utils.filters import RecipeFilter
        
        # Initialize filter with default metadata path
        recipe_filter = RecipeFilter()
        
        # Get available filters from actual data
        filters = recipe_filter.get_available_filters()
        
        return {
            "cuisines": filters["cuisines"],
            "diets": filters["diets"]
        }
        
    except Exception as e:
        # Fallback to hardcoded options if metadata loading fails
        return {
            "cuisines": [
                "Italian", "Asian", "Mexican", "American", "French", 
                "Indian", "Mediterranean", "Thai", "Chinese", "Japanese"
            ],
            "diets": [
                "vegetarian", "vegan", "gluten-free", "dairy-free", 
                "low-carb", "keto", "paleo", "pescatarian"
            ]
        }