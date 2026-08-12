"""
Pydantic models for API request and response validation.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class RecommendationRequest(BaseModel):
    """Request model for recipe recommendations."""
    
    ingredients: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=20,
        description="List of available ingredients"
    )
    cuisine_filter: Optional[str] = Field(
        None,
        description="Filter by cuisine type (e.g., 'Italian', 'Asian')"
    )
    diet_filter: Optional[str] = Field(
        None,
        description="Filter by diet type (e.g., 'vegetarian', 'vegan')"
    )
    max_results: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of recommendations to return"
    )
    
    @validator('ingredients')
    def validate_ingredients(cls, v):
        """Validate ingredients list."""
        if not v:
            raise ValueError("At least one ingredient is required")
        
        # Clean and validate each ingredient
        cleaned = []
        for ingredient in v:
            if not isinstance(ingredient, str):
                raise ValueError("All ingredients must be strings")
            
            cleaned_ingredient = ingredient.strip()
            if not cleaned_ingredient:
                continue
                
            if len(cleaned_ingredient) > 100:
                raise ValueError("Ingredient names must be less than 100 characters")
                
            cleaned.append(cleaned_ingredient)
        
        if not cleaned:
            raise ValueError("At least one valid ingredient is required")
            
        return cleaned
    
    @validator('cuisine_filter')
    def validate_cuisine(cls, v):
        """Validate cuisine filter."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v
    
    @validator('diet_filter')
    def validate_diet(cls, v):
        """Validate diet filter."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class RecipeResult(BaseModel):
    """Individual recipe result model."""
    
    id: int = Field(..., description="Recipe ID")
    title: str = Field(..., description="Recipe title")
    ingredients: List[str] = Field(..., description="Recipe ingredients")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    diet: Optional[str] = Field(None, description="Diet type")
    cooking_time: Optional[int] = Field(None, description="Cooking time in minutes")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Match percentage (0-1)")
    tfidf_score: Optional[float] = Field(None, description="TF-IDF similarity score")
    embedding_score: Optional[float] = Field(None, description="Embedding similarity score")


class RecommendationResponse(BaseModel):
    """Response model for recipe recommendations."""
    
    recipes: List[RecipeResult] = Field(..., description="List of recommended recipes")
    total_found: int = Field(..., description="Total number of recipes found")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_info: dict = Field(..., description="Information about models used")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    models_loaded: dict = Field(..., description="Status of loaded models")
    uptime: float = Field(..., description="Service uptime in seconds")