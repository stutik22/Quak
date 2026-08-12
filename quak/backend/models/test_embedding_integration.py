"""
Integration tests for the embedding-based recommender with real models.
"""

import pytest
import numpy as np
import os
from pathlib import Path

from recommender_embed import EmbeddingRecommender, get_embedding_recommender


class TestEmbeddingIntegration:
    """Integration tests with real model files."""
    
    @pytest.fixture
    def models_dir(self):
        """Get the models directory path."""
        return str(Path(__file__).parent)
    
    @pytest.fixture
    def recommender(self, models_dir):
        """Create a recommender instance."""
        return EmbeddingRecommender(models_dir)
    
    def test_model_files_exist(self, models_dir):
        """Test that all required model files exist."""
        models_path = Path(models_dir)
        
        required_files = [
            "recipe_vectors_embed.npy",
            "recipe_faiss_index.bin",
            "embedding_metadata.pkl",
            "recipe_metadata.pkl"
        ]
        
        for file_name in required_files:
            file_path = models_path / file_name
            assert file_path.exists(), f"Required file {file_name} not found in {models_dir}"
    
    def test_load_models_real(self, recommender):
        """Test loading real model files."""
        # Should not be loaded initially
        assert not recommender._is_loaded
        
        # Load models
        recommender.load_models()
        
        # Should be loaded now
        assert recommender._is_loaded
        assert recommender._embedding_model is not None
        assert recommender._faiss_index is not None
        assert recommender._recipe_metadata is not None
        assert recommender._embedding_metadata is not None
        
        # Check model properties
        assert len(recommender._recipe_metadata) > 0
        assert recommender._faiss_index.ntotal > 0
        assert recommender._embedding_vectors.shape[1] == 384  # MiniLM-L6-v2 dimension
    
    def test_get_recommendations_real(self, recommender):
        """Test getting recommendations with real models."""
        recommender.load_models()
        
        # Test with chicken-based ingredients
        ingredients = ["chicken", "garlic", "onion"]
        recommendations = recommender.get_top_recommendations(ingredients, top_n=3)
        
        # Should return recommendations
        assert len(recommendations) > 0
        assert len(recommendations) <= 3
        
        # Check recommendation structure
        for rec in recommendations:
            assert 'recipe_id' in rec
            assert 'title' in rec
            assert 'ingredients' in rec
            assert 'similarity_score' in rec
            assert 'match_percentage' in rec
            assert 0 <= rec['similarity_score'] <= 1
            assert 0 <= rec['match_percentage'] <= 100
        
        # Should be sorted by similarity score
        scores = [rec['similarity_score'] for rec in recommendations]
        assert scores == sorted(scores, reverse=True)
        
        print(f"\\nRecommendations for {ingredients}:")
        for i, rec in enumerate(recommendations):
            print(f"{i+1}. {rec['title']} (Score: {rec['similarity_score']:.4f})")
            print(f"   Ingredients: {rec['ingredients']}")
    
    def test_get_recommendations_fast_real(self, recommender):
        """Test fast recommendations with real models."""
        recommender.load_models()
        
        ingredients = ["tomato", "cheese", "pasta"]
        recommendations = recommender.get_top_recommendations_fast(ingredients, top_n=2)
        
        # Should return recommendations
        assert len(recommendations) > 0
        assert len(recommendations) <= 2
        
        # Check that results are valid
        for rec in recommendations:
            assert rec['similarity_score'] > 0
            assert rec['title'] != ''
        
        print(f"\\nFast recommendations for {ingredients}:")
        for i, rec in enumerate(recommendations):
            print(f"{i+1}. {rec['title']} (Score: {rec['similarity_score']:.4f})")
    
    def test_cuisine_filter_real(self, recommender):
        """Test cuisine filtering with real data."""
        recommender.load_models()
        
        ingredients = ["chicken", "spice"]
        
        # Get all recommendations
        all_recs = recommender.get_top_recommendations(ingredients, top_n=10)
        
        # Get Italian recommendations only
        italian_recs = recommender.get_top_recommendations(
            ingredients, top_n=10, cuisine_filter="Italian"
        )
        
        # Italian recommendations should be subset of all recommendations
        assert len(italian_recs) <= len(all_recs)
        
        # All Italian recommendations should have Italian cuisine
        for rec in italian_recs:
            assert rec['cuisine'].lower() == 'italian'
        
        print(f"\\nAll recommendations: {len(all_recs)}")
        print(f"Italian recommendations: {len(italian_recs)}")
    
    def test_diet_filter_real(self, recommender):
        """Test diet filtering with real data."""
        recommender.load_models()
        
        ingredients = ["vegetables", "healthy"]
        
        # Get vegan recommendations
        vegan_recs = recommender.get_top_recommendations(
            ingredients, top_n=10, diet_filter="Vegan"
        )
        
        # All vegan recommendations should contain "vegan" in diet types
        for rec in vegan_recs:
            assert 'vegan' in rec['diet_types'].lower()
        
        print(f"\\nVegan recommendations: {len(vegan_recs)}")
        for rec in vegan_recs:
            print(f"- {rec['title']} ({rec['diet_types']})")
    
    def test_similar_recipes_real(self, recommender):
        """Test finding similar recipes with real data."""
        recommender.load_models()
        
        # Get a recipe ID (use the first one)
        recipe_id = recommender._recipe_metadata[0]['id']
        original_recipe = recommender.get_recipe_by_id(recipe_id)
        
        # Find similar recipes
        similar_recipes = recommender.get_similar_recipes(recipe_id, top_n=3)
        
        # Should return similar recipes
        assert len(similar_recipes) > 0
        assert len(similar_recipes) <= 3
        
        # Should not include the original recipe
        for rec in similar_recipes:
            assert rec['recipe_id'] != recipe_id
        
        print(f"\\nOriginal recipe: {original_recipe['title']}")
        print(f"Ingredients: {original_recipe['ingredients_cleaned']}")
        print("\\nSimilar recipes:")
        for i, rec in enumerate(similar_recipes):
            print(f"{i+1}. {rec['title']} (Score: {rec['similarity_score']:.4f})")
    
    def test_benchmark_performance_real(self, recommender):
        """Test performance benchmarking with real models."""
        recommender.load_models()
        
        test_ingredients = ["chicken", "garlic", "onion", "tomato"]
        metrics = recommender.benchmark_performance(test_ingredients, num_runs=5)
        
        # Should return valid metrics
        assert metrics['embedding_time_ms'] > 0
        assert metrics['search_time_ms'] > 0
        assert metrics['total_time_ms'] > 0
        assert metrics['num_recipes'] > 0
        assert metrics['embedding_dimension'] == 384
        
        print(f"\\nPerformance metrics:")
        print(f"Embedding time: {metrics['embedding_time_ms']:.2f} ms")
        print(f"Search time: {metrics['search_time_ms']:.2f} ms")
        print(f"Total time: {metrics['total_time_ms']:.2f} ms")
        print(f"Recipes: {metrics['num_recipes']}")
    
    def test_model_info_real(self, recommender):
        """Test model information with real models."""
        recommender.load_models()
        
        info = recommender.get_model_info()
        
        # Should contain expected information
        assert info['model_type'] == 'Embedding (Sentence-BERT + FAISS)'
        assert info['is_loaded']
        assert info['num_recipes'] > 0
        assert info['embedding_dimension'] == 384
        assert info['model_name'] == 'all-MiniLM-L6-v2'
        assert info['faiss_index_size'] > 0
        
        print(f"\\nModel info:")
        for key, value in info.items():
            print(f"{key}: {value}")
    
    def test_empty_ingredients_real(self, recommender):
        """Test behavior with empty ingredients."""
        recommender.load_models()
        
        # Empty ingredients should return empty results
        recommendations = recommender.get_top_recommendations([])
        assert len(recommendations) == 0
        
        # Whitespace-only ingredients should also return empty results
        recommendations = recommender.get_top_recommendations(["", "  ", "   "])
        assert len(recommendations) == 0
    
    def test_global_recommender_real(self, models_dir):
        """Test the global recommender instance with real models."""
        # Clear any existing instance
        import recommender_embed
        recommender_embed._embedding_recommender = None
        
        # Get global instance
        recommender = get_embedding_recommender(models_dir)
        
        # Should work with real models
        recommender.load_models()
        assert recommender._is_loaded
        
        # Test a simple recommendation
        recommendations = recommender.get_top_recommendations(["pasta", "cheese"], top_n=1)
        assert len(recommendations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])