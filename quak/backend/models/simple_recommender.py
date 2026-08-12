"""
Simple recipe recommender that works without complex imports.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class SimpleRecommender:
    """Simple recommender that returns mock data for testing."""
    
    def __init__(self):
        """Initialize the simple recommender."""
        self.is_loaded = True
        logger.info("Simple recommender initialized")
    
    def get_recommendations(
        self,
        ingredients: List[str],
        cuisine_filter: Optional[str] = None,
        diet_filter: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get mock recommendations for testing.
        
        Args:
            ingredients: List of available ingredients
            cuisine_filter: Optional cuisine type filter
            diet_filter: Optional diet type filter
            max_results: Maximum number of results to return
            
        Returns:
            List of mock recipe recommendations
        """
        logger.info(f"Getting recommendations for ingredients: {ingredients}")
        
        # Mock recipe data
        mock_recipes = [
            {
                "id": 1,
                "title": "Tomato Basil Pasta",
                "ingredients": ["pasta", "tomatoes", "basil", "garlic", "olive oil"],
                "cuisine": "Italian",
                "diet": "vegetarian",
                "cooking_time": 20,
                "difficulty": "Easy",
                "match_score": 0.95,
                "tfidf_score": 0.92,
                "embedding_score": 0.98
            },
            {
                "id": 2,
                "title": "Chicken Stir Fry",
                "ingredients": ["chicken", "vegetables", "soy sauce", "ginger", "garlic"],
                "cuisine": "Asian",
                "diet": None,
                "cooking_time": 15,
                "difficulty": "Easy",
                "match_score": 0.88,
                "tfidf_score": 0.85,
                "embedding_score": 0.91
            },
            {
                "id": 3,
                "title": "Vegetable Curry",
                "ingredients": ["vegetables", "curry powder", "coconut milk", "onions", "garlic"],
                "cuisine": "Indian",
                "diet": "vegetarian",
                "cooking_time": 30,
                "difficulty": "Medium",
                "match_score": 0.82,
                "tfidf_score": 0.80,
                "embedding_score": 0.84
            },
            {
                "id": 4,
                "title": "Greek Salad",
                "ingredients": ["tomatoes", "cucumber", "olives", "feta cheese", "olive oil"],
                "cuisine": "Mediterranean",
                "diet": "vegetarian",
                "cooking_time": 10,
                "difficulty": "Easy",
                "match_score": 0.75,
                "tfidf_score": 0.72,
                "embedding_score": 0.78
            },
            {
                "id": 5,
                "title": "Beef Tacos",
                "ingredients": ["beef", "tortillas", "onions", "tomatoes", "cheese"],
                "cuisine": "Mexican",
                "diet": None,
                "cooking_time": 25,
                "difficulty": "Medium",
                "match_score": 0.70,
                "tfidf_score": 0.68,
                "embedding_score": 0.72
            }
        ]
        
        # Filter by cuisine if specified
        if cuisine_filter and cuisine_filter.lower() != "any":
            mock_recipes = [r for r in mock_recipes if r.get("cuisine", "").lower() == cuisine_filter.lower()]
        
        # Filter by diet if specified
        if diet_filter and diet_filter.lower() != "any":
            mock_recipes = [r for r in mock_recipes if r.get("diet", "").lower() == diet_filter.lower()]
        
        # Simple ingredient matching - boost score if ingredients match
        for recipe in mock_recipes:
            recipe_ingredients = [ing.lower() for ing in recipe["ingredients"]]
            input_ingredients = [ing.lower().strip() for ing in ingredients]
            
            # Count matching ingredients
            matches = sum(1 for ing in input_ingredients if any(ing in recipe_ing for recipe_ing in recipe_ingredients))
            
            if matches > 0:
                # Boost score based on matches
                boost = min(matches * 0.1, 0.3)
                recipe["match_score"] = min(recipe["match_score"] + boost, 1.0)
        
        # Sort by match score and return top results
        mock_recipes.sort(key=lambda x: x["match_score"], reverse=True)
        
        return mock_recipes[:max_results]
    
    def is_available(self) -> bool:
        """Check if the recommender is available."""
        return self.is_loaded
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            'simple_recommender': True,
            'tfidf_available': False,
            'embedding_available': False,
            'status': 'mock_data_mode'
        }


# Global instance
_simple_recommender = None

def get_simple_recommender() -> SimpleRecommender:
    """Get the global simple recommender instance."""
    global _simple_recommender
    if _simple_recommender is None:
        _simple_recommender = SimpleRecommender()
    return _simple_recommender