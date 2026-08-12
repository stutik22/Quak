"""
TF-IDF based recipe recommendation service.
Provides ingredient-based recipe matching using TF-IDF vectorization and cosine similarity.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple, Optional
import logging
try:
    from .load_models import get_model_loader
except ImportError:
    from models.load_models import get_model_loader

logger = logging.getLogger(__name__)

class TFIDFRecommender:
    """TF-IDF based recipe recommender."""
    
    def __init__(self, models_dir: str = "models"):
        """
        Initialize the TF-IDF recommender.
        
        Args:
            models_dir: Directory containing model files
        """
        self.models_dir = models_dir
        self.model_loader = get_model_loader(models_dir)
        self._vectorizer = None
        self._recipe_vectors = None
        self._recipe_metadata = None
        self._is_loaded = False
    
    def load_models(self):
        """Load all required models and data."""
        if self._is_loaded:
            return
            
        try:
            logger.info("Loading TF-IDF models...")
            self._vectorizer, self._recipe_vectors, self._recipe_metadata = (
                self.model_loader.load_all_tfidf_components()
            )
            self._is_loaded = True
            logger.info(f"Successfully loaded TF-IDF models. {len(self._recipe_metadata)} recipes available.")
        except Exception as e:
            logger.error(f"Failed to load TF-IDF models: {e}")
            raise
    
    def _preprocess_ingredients(self, ingredients: List[str]) -> str:
        """
        Preprocess input ingredients to match training format.
        
        Args:
            ingredients: List of ingredient strings
            
        Returns:
            Comma-separated string of ingredients
        """
        # Clean and normalize ingredients
        cleaned_ingredients = []
        for ingredient in ingredients:
            # Basic cleaning - lowercase and strip
            cleaned = ingredient.lower().strip()
            if cleaned:
                cleaned_ingredients.append(cleaned)
        
        return ','.join(cleaned_ingredients)
    
    def compute_similarity_scores(self, ingredients: List[str]) -> np.ndarray:
        """
        Compute similarity scores for given ingredients against all recipes.
        
        Args:
            ingredients: List of ingredient strings
            
        Returns:
            Array of similarity scores for each recipe
            
        Raises:
            RuntimeError: If models are not loaded
        """
        if not self._is_loaded:
            self.load_models()
        
        # Preprocess ingredients
        ingredient_text = self._preprocess_ingredients(ingredients)
        
        if not ingredient_text:
            logger.warning("No valid ingredients provided")
            return np.zeros(len(self._recipe_metadata))
        
        try:
            # Transform ingredients using the trained vectorizer
            query_vector = self._vectorizer.transform([ingredient_text])
            
            # Compute cosine similarity with all recipe vectors
            similarities = cosine_similarity(query_vector, self._recipe_vectors).flatten()
            
            logger.debug(f"Computed similarities for {len(similarities)} recipes")
            return similarities
            
        except Exception as e:
            logger.error(f"Error computing similarities: {e}")
            raise
    
    def get_top_recommendations(
        self, 
        ingredients: List[str], 
        top_n: int = 10,
        min_score: float = 0.0,
        cuisine_filter: Optional[str] = None,
        diet_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top recipe recommendations based on ingredients.
        
        Args:
            ingredients: List of ingredient strings
            top_n: Number of top recommendations to return
            min_score: Minimum similarity score threshold
            cuisine_filter: Optional cuisine type filter
            diet_filter: Optional diet type filter
            
        Returns:
            List of recommendation dictionaries with recipe info and scores
        """
        if not self._is_loaded:
            self.load_models()
        
        # Compute similarity scores
        similarities = self.compute_similarity_scores(ingredients)
        
        # Create recommendations with metadata
        recommendations = []
        for idx, score in enumerate(similarities):
            if score < min_score:
                continue
                
            recipe = self._recipe_metadata[idx]
            
            # Apply filters
            if cuisine_filter and recipe.get('cuisine', '').lower() != cuisine_filter.lower():
                continue
                
            if diet_filter and diet_filter.lower() not in recipe.get('diet_types', '').lower():
                continue
            
            recommendations.append({
                'recipe_id': recipe.get('id', idx),
                'title': recipe.get('title', 'Unknown'),
                'ingredients': recipe.get('ingredients_cleaned', ''),
                'cuisine': recipe.get('cuisine', 'Unknown'),
                'diet_types': recipe.get('diet_types', ''),
                'cooking_time': recipe.get('cooking_time', 0),
                'difficulty': recipe.get('difficulty', 'Unknown'),
                'similarity_score': float(score),
                'match_percentage': float(score * 100)
            })
        
        # Sort by similarity score (descending) and return top N
        recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        logger.info(f"Generated {len(recommendations[:top_n])} recommendations from {len(recommendations)} candidates")
        return recommendations[:top_n]
    
    def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Get recipe details by ID.
        
        Args:
            recipe_id: Recipe ID to lookup
            
        Returns:
            Recipe dictionary or None if not found
        """
        if not self._is_loaded:
            self.load_models()
        
        for recipe in self._recipe_metadata:
            if recipe.get('id') == recipe_id:
                return recipe
        
        return None
    
    def get_similar_recipes(self, recipe_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Find recipes similar to a given recipe.
        
        Args:
            recipe_id: ID of the reference recipe
            top_n: Number of similar recipes to return
            
        Returns:
            List of similar recipe recommendations
        """
        if not self._is_loaded:
            self.load_models()
        
        # Find the recipe
        recipe = self.get_recipe_by_id(recipe_id)
        if not recipe:
            logger.warning(f"Recipe with ID {recipe_id} not found")
            return []
        
        # Use the recipe's ingredients to find similar recipes
        ingredients = recipe.get('ingredients_cleaned', '').split(',')
        ingredients = [ing.strip() for ing in ingredients if ing.strip()]
        
        # Get recommendations and exclude the original recipe
        recommendations = self.get_top_recommendations(ingredients, top_n + 1)
        similar_recipes = [rec for rec in recommendations if rec['recipe_id'] != recipe_id]
        
        return similar_recipes[:top_n]
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        info = {
            'model_type': 'TF-IDF',
            'is_loaded': self._is_loaded,
            'models_dir': self.models_dir
        }
        
        if self._is_loaded:
            info.update({
                'num_recipes': len(self._recipe_metadata),
                'vocabulary_size': len(self._vectorizer.vocabulary_),
                'vector_dimensions': self._recipe_vectors.shape[1] if self._recipe_vectors is not None else 0
            })
        
        return info


# Global recommender instance
_tfidf_recommender = None

def get_tfidf_recommender(models_dir: str = "models") -> TFIDFRecommender:
    """
    Get the global TF-IDF recommender instance.
    
    Args:
        models_dir: Directory containing model files
        
    Returns:
        TFIDFRecommender instance
    """
    global _tfidf_recommender
    if _tfidf_recommender is None:
        _tfidf_recommender = TFIDFRecommender(models_dir)
    return _tfidf_recommender