"""
Embedding-based recipe recommendation service.
Provides ingredient-based recipe matching using Sentence-BERT embeddings and FAISS similarity search.
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple, Optional
import logging
import time
try:
    from .load_models import get_model_loader
except ImportError:
    from models.load_models import get_model_loader

logger = logging.getLogger(__name__)

class EmbeddingRecommender:
    """Embedding-based recipe recommender using Sentence-BERT and FAISS."""
    
    def __init__(self, models_dir: str = "models"):
        """
        Initialize the embedding recommender.
        
        Args:
            models_dir: Directory containing model files
        """
        self.models_dir = models_dir
        self.model_loader = get_model_loader(models_dir)
        self._embedding_model = None
        self._embedding_vectors = None
        self._faiss_index = None
        self._recipe_metadata = None
        self._embedding_metadata = None
        self._is_loaded = False
    
    def load_models(self):
        """Load all required models and data."""
        if self._is_loaded:
            return
            
        try:
            logger.info("Loading embedding models...")
            (self._embedding_model, self._embedding_vectors, self._faiss_index, 
             self._recipe_metadata, self._embedding_metadata) = (
                self.model_loader.load_all_embedding_components()
            )
            self._is_loaded = True
            logger.info(f"Successfully loaded embedding models. {len(self._recipe_metadata)} recipes available.")
        except Exception as e:
            logger.error(f"Failed to load embedding models: {e}")
            raise
    
    def _preprocess_ingredients(self, ingredients: List[str]) -> str:
        """
        Preprocess input ingredients to match training format.
        
        Args:
            ingredients: List of ingredient strings
            
        Returns:
            Space-separated string of ingredients for embedding
        """
        # Clean and normalize ingredients
        cleaned_ingredients = []
        for ingredient in ingredients:
            # Basic cleaning - lowercase and strip
            cleaned = ingredient.lower().strip()
            if cleaned:
                cleaned_ingredients.append(cleaned)
        
        # Convert to space-separated format for embedding (same as training)
        return ' '.join(cleaned_ingredients)
    
    def compute_similarity_scores(self, ingredients: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute similarity scores for given ingredients against all recipes using FAISS.
        
        Args:
            ingredients: List of ingredient strings
            
        Returns:
            Tuple of (similarity_scores, recipe_indices) for all recipes
            
        Raises:
            RuntimeError: If models are not loaded
        """
        if not self._is_loaded:
            self.load_models()
        
        # Preprocess ingredients
        ingredient_text = self._preprocess_ingredients(ingredients)
        
        if not ingredient_text:
            logger.warning("No valid ingredients provided")
            # Return zeros for all recipes
            num_recipes = len(self._recipe_metadata)
            return np.zeros(num_recipes), np.arange(num_recipes)
        
        try:
            # Generate embedding for query ingredients
            query_embedding = self._embedding_model.encode([ingredient_text], convert_to_numpy=True)
            
            # Normalize for cosine similarity (same as training)
            faiss.normalize_L2(query_embedding)
            
            # Search all recipes using FAISS
            num_recipes = len(self._recipe_metadata)
            similarities, indices = self._faiss_index.search(query_embedding, num_recipes)
            
            # FAISS returns results sorted by similarity, but we need all recipes with their scores
            # Create a full similarity array
            full_similarities = np.zeros(num_recipes)
            for i, (sim, idx) in enumerate(zip(similarities[0], indices[0])):
                full_similarities[idx] = sim
            
            logger.debug(f"Computed similarities for {len(full_similarities)} recipes")
            return full_similarities, np.arange(num_recipes)
            
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
        Get top recipe recommendations based on ingredients using embedding similarity.
        
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
        
        # Check if ingredients are empty after preprocessing
        ingredient_text = self._preprocess_ingredients(ingredients)
        if not ingredient_text:
            logger.warning("No valid ingredients provided for recommendations")
            return []
        
        # Compute similarity scores
        similarities, _ = self.compute_similarity_scores(ingredients)
        
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
    
    def get_top_recommendations_fast(
        self, 
        ingredients: List[str], 
        top_n: int = 10,
        min_score: float = 0.0,
        cuisine_filter: Optional[str] = None,
        diet_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top recipe recommendations using FAISS for efficient top-k search.
        This is more efficient than get_top_recommendations for small top_n values.
        
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
        
        # Preprocess ingredients
        ingredient_text = self._preprocess_ingredients(ingredients)
        
        if not ingredient_text:
            logger.warning("No valid ingredients provided for fast recommendations")
            return []
        
        try:
            # Generate embedding for query ingredients
            query_embedding = self._embedding_model.encode([ingredient_text], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)
            
            # Search for more candidates than needed to account for filtering
            search_k = min(top_n * 3, len(self._recipe_metadata))
            similarities, indices = self._faiss_index.search(query_embedding, search_k)
            
            # Create recommendations with metadata
            recommendations = []
            for sim, idx in zip(similarities[0], indices[0]):
                if sim < min_score:
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
                    'similarity_score': float(sim),
                    'match_percentage': float(sim * 100)
                })
                
                # Stop if we have enough recommendations
                if len(recommendations) >= top_n:
                    break
            
            logger.info(f"Generated {len(recommendations)} fast recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in fast recommendations: {e}")
            raise
    
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
        Find recipes similar to a given recipe using embeddings.
        
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
        recommendations = self.get_top_recommendations_fast(ingredients, top_n + 1)
        similar_recipes = [rec for rec in recommendations if rec['recipe_id'] != recipe_id]
        
        return similar_recipes[:top_n]
    
    def benchmark_performance(self, test_ingredients: List[str], num_runs: int = 10) -> Dict[str, float]:
        """
        Benchmark the performance of the embedding recommender.
        
        Args:
            test_ingredients: List of ingredients to test with
            num_runs: Number of runs for averaging
            
        Returns:
            Dictionary with performance metrics
        """
        if not self._is_loaded:
            self.load_models()
        
        # Warm up
        self.get_top_recommendations_fast(test_ingredients, top_n=5)
        
        # Benchmark embedding generation
        start_time = time.perf_counter()
        for _ in range(num_runs):
            ingredient_text = self._preprocess_ingredients(test_ingredients)
            query_embedding = self._embedding_model.encode([ingredient_text], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)
        embedding_time = (time.perf_counter() - start_time) / num_runs
        
        # Benchmark FAISS search
        ingredient_text = self._preprocess_ingredients(test_ingredients)
        query_embedding = self._embedding_model.encode([ingredient_text], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        
        start_time = time.perf_counter()
        for _ in range(num_runs):
            self._faiss_index.search(query_embedding, 10)
        search_time = (time.perf_counter() - start_time) / num_runs
        
        # Benchmark full recommendation pipeline
        start_time = time.perf_counter()
        for _ in range(num_runs):
            self.get_top_recommendations_fast(test_ingredients, top_n=10)
        total_time = (time.perf_counter() - start_time) / num_runs
        
        return {
            'embedding_time_ms': embedding_time * 1000,
            'search_time_ms': search_time * 1000,
            'total_time_ms': total_time * 1000,
            'num_recipes': len(self._recipe_metadata),
            'embedding_dimension': self._embedding_metadata.get('embedding_dimension', 0)
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        info = {
            'model_type': 'Embedding (Sentence-BERT + FAISS)',
            'is_loaded': self._is_loaded,
            'models_dir': self.models_dir
        }
        
        if self._is_loaded:
            info.update({
                'num_recipes': len(self._recipe_metadata),
                'embedding_dimension': self._embedding_metadata.get('embedding_dimension', 0),
                'model_name': self._embedding_metadata.get('model_name', 'unknown'),
                'faiss_index_size': self._faiss_index.ntotal if self._faiss_index else 0,
                'index_type': self._embedding_metadata.get('index_type', 'unknown')
            })
        
        return info


# Global recommender instance
_embedding_recommender = None

def get_embedding_recommender(models_dir: str = "models") -> EmbeddingRecommender:
    """
    Get the global embedding recommender instance.
    
    Args:
        models_dir: Directory containing model files
        
    Returns:
        EmbeddingRecommender instance
    """
    global _embedding_recommender
    if _embedding_recommender is None:
        _embedding_recommender = EmbeddingRecommender(models_dir)
    return _embedding_recommender