"""
Similarity computation utilities for hybrid recipe recommendation.
Combines TF-IDF and embedding-based similarity scores with configurable weights.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
try:
    from ..core.config import settings
except ImportError:
    from core.config import settings

logger = logging.getLogger(__name__)


class HybridScorer:
    """Hybrid scoring system that combines TF-IDF and embedding similarity scores."""
    
    def __init__(
        self, 
        tfidf_weight: float = None, 
        embedding_weight: float = None,
        normalize_scores: bool = True
    ):
        """
        Initialize the hybrid scorer.
        
        Args:
            tfidf_weight: Weight for TF-IDF scores (default from settings)
            embedding_weight: Weight for embedding scores (default from settings)
            normalize_scores: Whether to normalize individual scores before combining
        """
        self.tfidf_weight = tfidf_weight or settings.tfidf_weight
        self.embedding_weight = embedding_weight or settings.embedding_weight
        self.normalize_scores = normalize_scores
        
        # Ensure weights sum to 1.0
        total_weight = self.tfidf_weight + self.embedding_weight
        if total_weight > 0:
            self.tfidf_weight /= total_weight
            self.embedding_weight /= total_weight
        else:
            # Fallback to equal weights
            self.tfidf_weight = 0.5
            self.embedding_weight = 0.5
            
        logger.info(f"Hybrid scorer initialized: TF-IDF={self.tfidf_weight:.2f}, Embedding={self.embedding_weight:.2f}")
    
    def normalize_score_array(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalize scores to 0-1 range using min-max normalization.
        
        Args:
            scores: Array of similarity scores
            
        Returns:
            Normalized scores in 0-1 range
        """
        if len(scores) == 0:
            return scores
            
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        if max_score == min_score:
            # All scores are the same, return array of 0.5s
            return np.full_like(scores, 0.5)
        
        return (scores - min_score) / (max_score - min_score)
    
    def combine_scores(
        self, 
        tfidf_scores: Optional[np.ndarray] = None,
        embedding_scores: Optional[np.ndarray] = None,
        recipe_ids: Optional[List[int]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Combine TF-IDF and embedding scores using weighted average.
        
        Args:
            tfidf_scores: TF-IDF similarity scores
            embedding_scores: Embedding similarity scores
            recipe_ids: Recipe IDs corresponding to scores (for debugging)
            
        Returns:
            Tuple of (combined_scores, score_info)
        """
        score_info = {
            "tfidf_available": tfidf_scores is not None,
            "embedding_available": embedding_scores is not None,
            "normalization_applied": self.normalize_scores,
            "weights": {
                "tfidf": self.tfidf_weight,
                "embedding": self.embedding_weight
            }
        }
        
        # Handle case where no scores are available
        if tfidf_scores is None and embedding_scores is None:
            logger.warning("No similarity scores available for combination")
            return np.array([]), score_info
        
        # Handle case where only one type of score is available
        if tfidf_scores is None:
            logger.info("Using embedding scores only (TF-IDF not available)")
            scores = embedding_scores
            if self.normalize_scores:
                scores = self.normalize_score_array(scores)
            score_info["fallback_mode"] = "embedding_only"
            return scores, score_info
            
        if embedding_scores is None:
            logger.info("Using TF-IDF scores only (embeddings not available)")
            scores = tfidf_scores
            if self.normalize_scores:
                scores = self.normalize_score_array(scores)
            score_info["fallback_mode"] = "tfidf_only"
            return scores, score_info
        
        # Ensure both score arrays have the same length
        if len(tfidf_scores) != len(embedding_scores):
            logger.error(f"Score array length mismatch: TF-IDF={len(tfidf_scores)}, Embedding={len(embedding_scores)}")
            # Use the shorter array length
            min_length = min(len(tfidf_scores), len(embedding_scores))
            tfidf_scores = tfidf_scores[:min_length]
            embedding_scores = embedding_scores[:min_length]
        
        # Normalize scores if requested
        if self.normalize_scores:
            tfidf_scores = self.normalize_score_array(tfidf_scores)
            embedding_scores = self.normalize_score_array(embedding_scores)
        
        # Combine scores using weighted average
        combined_scores = (
            self.tfidf_weight * tfidf_scores + 
            self.embedding_weight * embedding_scores
        )
        
        score_info["combination_method"] = "weighted_average"
        score_info["score_statistics"] = {
            "tfidf_mean": float(np.mean(tfidf_scores)),
            "tfidf_std": float(np.std(tfidf_scores)),
            "embedding_mean": float(np.mean(embedding_scores)),
            "embedding_std": float(np.std(embedding_scores)),
            "combined_mean": float(np.mean(combined_scores)),
            "combined_std": float(np.std(combined_scores))
        }
        
        logger.debug(f"Combined {len(combined_scores)} scores using hybrid method")
        
        return combined_scores, score_info
    
    def rank_recipes(
        self, 
        recipes: List[Dict[str, Any]], 
        combined_scores: np.ndarray,
        top_n: int = None
    ) -> List[Dict[str, Any]]:
        """
        Rank recipes by combined similarity scores.
        
        Args:
            recipes: List of recipe dictionaries
            combined_scores: Combined similarity scores
            top_n: Number of top recipes to return (None for all)
            
        Returns:
            List of ranked recipes with similarity scores
        """
        if len(recipes) != len(combined_scores):
            logger.error(f"Recipe count mismatch: {len(recipes)} recipes, {len(combined_scores)} scores")
            min_length = min(len(recipes), len(combined_scores))
            recipes = recipes[:min_length]
            combined_scores = combined_scores[:min_length]
        
        # Create list of (recipe, score) tuples
        recipe_score_pairs = list(zip(recipes, combined_scores))
        
        # Sort by score in descending order
        ranked_pairs = sorted(recipe_score_pairs, key=lambda x: x[1], reverse=True)
        
        # Extract ranked recipes and add similarity scores
        ranked_recipes = []
        for recipe, score in ranked_pairs:
            recipe_with_score = recipe.copy()
            recipe_with_score['similarity_score'] = float(score)
            ranked_recipes.append(recipe_with_score)
        
        # Return top N if specified
        if top_n is not None:
            ranked_recipes = ranked_recipes[:top_n]
        
        logger.debug(f"Ranked {len(ranked_recipes)} recipes by similarity score")
        
        return ranked_recipes


def create_hybrid_scorer(
    tfidf_weight: float = None, 
    embedding_weight: float = None
) -> HybridScorer:
    """
    Factory function to create a hybrid scorer with optional custom weights.
    
    Args:
        tfidf_weight: Custom TF-IDF weight (uses settings default if None)
        embedding_weight: Custom embedding weight (uses settings default if None)
        
    Returns:
        Configured HybridScorer instance
    """
    return HybridScorer(
        tfidf_weight=tfidf_weight,
        embedding_weight=embedding_weight
    )