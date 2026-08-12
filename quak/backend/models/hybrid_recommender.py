"""
Hybrid recipe recommendation service that combines TF-IDF and embedding-based models.
Provides fallback logic and configurable model weights for optimal recommendation accuracy.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
import time

try:
    from .recommender_tfidf import get_tfidf_recommender
    from .recommender_embed import get_embedding_recommender
    from ..utils.similarity import HybridScorer, create_hybrid_scorer
    from ..core.config import settings
except ImportError:
    from models.recommender_tfidf import get_tfidf_recommender
    from models.recommender_embed import get_embedding_recommender
    from utils.similarity import HybridScorer, create_hybrid_scorer
    from core.config import settings

logger = logging.getLogger(__name__)


class HybridRecommender:
    """
    Hybrid recommendation system that combines TF-IDF and embedding-based approaches.
    """
    
    def __init__(self):
        """Initialize the hybrid recommender."""
        self.tfidf_recommender = None
        self.embedding_recommender = None
        self.hybrid_scorer = None
        self.tfidf_weight = settings.tfidf_weight
        self.embedding_weight = settings.embedding_weight
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize the underlying recommendation models."""
        try:
            # Initialize TF-IDF recommender
            self.tfidf_recommender = get_tfidf_recommender()
            logger.info("TF-IDF recommender initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TF-IDF recommender: {e}")
        
        try:
            # Initialize embedding recommender
            self.embedding_recommender = get_embedding_recommender()
            logger.info("Embedding recommender initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embedding recommender: {e}")
        
        try:
            # Initialize hybrid scorer
            self.hybrid_scorer = create_hybrid_scorer(
                tfidf_weight=self.tfidf_weight,
                embedding_weight=self.embedding_weight
            )
            logger.info("Hybrid scorer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize hybrid scorer: {e}")
    
    def get_recommendations(
        self,
        ingredients: List[str],
        cuisine_filter: Optional[str] = None,
        diet_filter: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get hybrid recommendations combining TF-IDF and embedding approaches.
        
        Args:
            ingredients: List of available ingredients
            cuisine_filter: Optional cuisine type filter
            diet_filter: Optional diet type filter
            max_results: Maximum number of results to return
            
        Returns:
            List of recipe recommendations with scores
        """
        start_time = time.time()
        
        # Get TF-IDF recommendations
        tfidf_results = []
        if self.tfidf_recommender:
            try:
                tfidf_results = self.tfidf_recommender.get_top_recommendations(
                    ingredients=ingredients,
                    cuisine_filter=cuisine_filter,
                    diet_filter=diet_filter,
                    top_n=max_results * 2  # Get more for better hybrid scoring
                )
            except Exception as e:
                logger.error(f"TF-IDF recommendation failed: {e}")
        
        # Get embedding recommendations
        embedding_results = []
        if self.embedding_recommender:
            try:
                embedding_results = self.embedding_recommender.get_top_recommendations(
                    ingredients=ingredients,
                    cuisine_filter=cuisine_filter,
                    diet_filter=diet_filter,
                    top_n=max_results * 2  # Get more for better hybrid scoring
                )
            except Exception as e:
                logger.error(f"Embedding recommendation failed: {e}")
        
        # Simple combination for now - just merge and sort by match_score
        all_results = []
        
        # Add TF-IDF results with source info
        for result in tfidf_results:
            result_copy = result.copy()
            result_copy['tfidf_score'] = result_copy.get('similarity_score', 0.0)
            result_copy['source'] = 'tfidf'
            all_results.append(result_copy)
        
        # Add embedding results with source info
        for result in embedding_results:
            result_copy = result.copy()
            result_copy['embedding_score'] = result_copy.get('similarity_score', 0.0)
            result_copy['source'] = 'embedding'
            all_results.append(result_copy)
        
        # Remove duplicates based on recipe ID and combine scores
        unique_results = {}
        for result in all_results:
            recipe_id = result.get('recipe_id')
            if recipe_id in unique_results:
                # Combine scores from both models
                existing = unique_results[recipe_id]
                if result['source'] == 'tfidf':
                    existing['tfidf_score'] = result.get('tfidf_score', 0.0)
                else:
                    existing['embedding_score'] = result.get('embedding_score', 0.0)
                
                # Calculate hybrid score
                tfidf_score = existing.get('tfidf_score', 0.0)
                embedding_score = existing.get('embedding_score', 0.0)
                existing['match_score'] = (
                    self.tfidf_weight * tfidf_score + 
                    self.embedding_weight * embedding_score
                )
            else:
                # Initialize scores
                if result['source'] == 'tfidf':
                    result['tfidf_score'] = result.get('tfidf_score', 0.0)
                    result['embedding_score'] = 0.0
                else:
                    result['tfidf_score'] = 0.0
                    result['embedding_score'] = result.get('embedding_score', 0.0)
                
                tfidf_score = result['tfidf_score']
                embedding_score = result['embedding_score']
                result['match_score'] = (
                    self.tfidf_weight * tfidf_score + 
                    self.embedding_weight * embedding_score
                )
                unique_results[recipe_id] = result
        
        # Convert back to list and sort by match_score
        combined_results = list(unique_results.values())
        combined_results.sort(key=lambda x: x.get('match_score', 0.0), reverse=True)
        combined_results = combined_results[:max_results]
        
        processing_time = time.time() - start_time
        logger.info(f"Hybrid recommendation completed in {processing_time:.3f}s")
        
        return combined_results
    
    def is_available(self) -> bool:
        """Check if the hybrid recommender is available."""
        return (self.tfidf_recommender is not None or 
                self.embedding_recommender is not None)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            'tfidf_available': self.tfidf_recommender is not None,
            'embedding_available': self.embedding_recommender is not None,
            'hybrid_scorer_available': self.hybrid_scorer is not None,
            'tfidf_weight': self.tfidf_weight,
            'embedding_weight': self.embedding_weight
        }


