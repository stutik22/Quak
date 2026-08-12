"""
Tests for the embedding-based recipe recommender.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from recommender_embed import EmbeddingRecommender, get_embedding_recommender


class TestEmbeddingRecommender:
    """Test cases for EmbeddingRecommender class."""
    
    @pytest.fixture
    def mock_models_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_recipe_metadata(self):
        """Sample recipe metadata for testing."""
        return [
            {
                'id': 0,
                'title': 'Spaghetti Carbonara',
                'ingredients_cleaned': 'spaghetti pasta,egg,bacon,parmesan cheese,black pepper,garlic',
                'cuisine': 'Italian',
                'diet_types': 'Regular',
                'cooking_time': 20,
                'difficulty': 'Medium'
            },
            {
                'id': 1,
                'title': 'Vegan Buddha Bowl',
                'ingredients_cleaned': 'quinoa,chickpea,avocado,spinach,cherry tomato,tahini,lemon juice',
                'cuisine': 'Other',
                'diet_types': 'Vegan,Gluten-Free',
                'cooking_time': 45,
                'difficulty': 'Easy'
            },
            {
                'id': 2,
                'title': 'Chicken Tikka Masala',
                'ingredients_cleaned': 'chicken breast,tomato,heavy cream,onion,garlic,ginger,garam masala,turmeric,cumin',
                'cuisine': 'Indian',
                'diet_types': 'Regular',
                'cooking_time': 90,
                'difficulty': 'Hard'
            }
        ]
    
    @pytest.fixture
    def sample_embeddings(self):
        """Sample embedding vectors for testing."""
        # Create 3 sample 384-dimensional embeddings
        np.random.seed(42)
        return np.random.rand(3, 384).astype(np.float32)
    
    @pytest.fixture
    def mock_embedding_metadata(self):
        """Sample embedding metadata for testing."""
        return {
            'model_name': 'all-MiniLM-L6-v2',
            'embedding_dimension': 384,
            'num_recipes': 3,
            'index_type': 'IndexFlatIP',
            'normalized': True
        }
    
    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock SentenceTransformer for testing."""
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)
        return mock_model
    
    @pytest.fixture
    def mock_faiss_index(self):
        """Mock FAISS index for testing."""
        mock_index = Mock()
        mock_index.ntotal = 3
        # Mock search results: (similarities, indices)
        mock_index.search.return_value = (
            np.array([[0.8, 0.6, 0.4]]),  # similarities
            np.array([[0, 1, 2]])         # indices
        )
        return mock_index
    
    @pytest.fixture
    def recommender_with_mocks(self, mock_models_dir, sample_recipe_metadata, 
                              sample_embeddings, mock_embedding_metadata,
                              mock_sentence_transformer, mock_faiss_index):
        """Create a recommender with mocked dependencies."""
        recommender = EmbeddingRecommender(mock_models_dir)
        
        # Mock the model loader
        mock_loader = Mock()
        mock_loader.load_all_embedding_components.return_value = (
            mock_sentence_transformer,
            sample_embeddings,
            mock_faiss_index,
            sample_recipe_metadata,
            mock_embedding_metadata
        )
        recommender.model_loader = mock_loader
        
        return recommender
    
    def test_init(self, mock_models_dir):
        """Test recommender initialization."""
        recommender = EmbeddingRecommender(mock_models_dir)
        
        assert recommender.models_dir == mock_models_dir
        assert not recommender._is_loaded
        assert recommender._embedding_model is None
        assert recommender._faiss_index is None
    
    def test_load_models(self, recommender_with_mocks):
        """Test model loading."""
        recommender = recommender_with_mocks
        
        # Initially not loaded
        assert not recommender._is_loaded
        
        # Load models
        recommender.load_models()
        
        # Should be loaded now
        assert recommender._is_loaded
        assert recommender._embedding_model is not None
        assert recommender._faiss_index is not None
        assert recommender._recipe_metadata is not None
        
        # Loading again should not reload
        recommender.model_loader.load_all_embedding_components.reset_mock()
        recommender.load_models()
        recommender.model_loader.load_all_embedding_components.assert_not_called()
    
    def test_preprocess_ingredients(self, recommender_with_mocks):
        """Test ingredient preprocessing."""
        recommender = recommender_with_mocks
        
        # Test normal ingredients
        ingredients = ["Chicken Breast", "  Garlic  ", "Onion"]
        result = recommender._preprocess_ingredients(ingredients)
        assert result == "chicken breast garlic onion"
        
        # Test empty ingredients
        ingredients = ["", "  ", None]
        result = recommender._preprocess_ingredients([ing for ing in ingredients if ing])
        assert result == ""
        
        # Test mixed case and punctuation
        ingredients = ["TOMATO", "bell-pepper", "olive oil"]
        result = recommender._preprocess_ingredients(ingredients)
        assert result == "tomato bell-pepper olive oil"
    
    def test_compute_similarity_scores(self, recommender_with_mocks):
        """Test similarity score computation."""
        recommender = recommender_with_mocks
        recommender.load_models()
        
        ingredients = ["chicken", "garlic", "onion"]
        similarities, indices = recommender.compute_similarity_scores(ingredients)
        
        # Should return scores for all recipes
        assert len(similarities) == 3
        assert len(indices) == 3
        assert isinstance(similarities, np.ndarray)
        assert isinstance(indices, np.ndarray)
        
        # Mock should have been called
        recommender._embedding_model.encode.assert_called_once()
        recommender._faiss_index.search.assert_called_once()
    
    def test_compute_similarity_scores_empty_ingredients(self, recommender_with_mocks):
        """Test similarity computation with empty ingredients."""
        recommender = recommender_with_mocks
        recommender.load_models()
        
        similarities, indices = recommender.compute_similarity_scores([])
        
        # Should return zeros for all recipes
        assert len(similarities) == 3
        assert np.all(similarities == 0)
    
    def test_get_top_recommendations(self, recommender_with_mocks):
        """Test getting top recommendations."""
        recommender = recommender_with_mocks
        
        ingredients = ["chicken", "garlic", "onion"]
        recommendations = recommender.get_top_recommendations(ingredients, top_n=2)
        
        # Should return recommendations
        assert len(recommendations) <= 2
        assert all('recipe_id' in rec for rec in recommendations)
        assert all('title' in rec for rec in recommendations)
        assert all('similarity_score' in rec for rec in recommendations)
        assert all('match_percentage' in rec for rec in recommendations)
        
        # Should be sorted by similarity score (descending)
        if len(recommendations) > 1:
            for i in range(len(recommendations) - 1):
                assert recommendations[i]['similarity_score'] >= recommendations[i + 1]['similarity_score']
    
    def test_get_top_recommendations_with_filters(self, recommender_with_mocks):
        """Test recommendations with cuisine and diet filters."""
        recommender = recommender_with_mocks
        
        ingredients = ["chicken", "garlic"]
        
        # Test cuisine filter
        recommendations = recommender.get_top_recommendations(
            ingredients, cuisine_filter="Italian"
        )
        # Should only return Italian recipes (if any match)
        for rec in recommendations:
            assert rec['cuisine'].lower() == 'italian'
        
        # Test diet filter
        recommendations = recommender.get_top_recommendations(
            ingredients, diet_filter="Vegan"
        )
        # Should only return vegan recipes (if any match)
        for rec in recommendations:
            assert 'vegan' in rec['diet_types'].lower()
    
    def test_get_top_recommendations_fast(self, recommender_with_mocks):
        """Test fast recommendations using FAISS top-k search."""
        recommender = recommender_with_mocks
        
        ingredients = ["chicken", "garlic", "onion"]
        recommendations = recommender.get_top_recommendations_fast(ingredients, top_n=2)
        
        # Should return recommendations
        assert len(recommendations) <= 2
        assert all('recipe_id' in rec for rec in recommendations)
        assert all('similarity_score' in rec for rec in recommendations)
        
        # Mock should have been called with appropriate k
        recommender._faiss_index.search.assert_called()
    
    def test_get_recipe_by_id(self, recommender_with_mocks, sample_recipe_metadata):
        """Test recipe lookup by ID."""
        recommender = recommender_with_mocks
        recommender.load_models()
        
        # Test existing recipe
        recipe = recommender.get_recipe_by_id(1)
        assert recipe is not None
        assert recipe['id'] == 1
        assert recipe['title'] == 'Vegan Buddha Bowl'
        
        # Test non-existing recipe
        recipe = recommender.get_recipe_by_id(999)
        assert recipe is None
    
    def test_get_similar_recipes(self, recommender_with_mocks):
        """Test finding similar recipes."""
        recommender = recommender_with_mocks
        
        similar_recipes = recommender.get_similar_recipes(recipe_id=0, top_n=2)
        
        # Should return similar recipes (excluding the original)
        assert len(similar_recipes) <= 2
        assert all(rec['recipe_id'] != 0 for rec in similar_recipes)
    
    def test_get_similar_recipes_invalid_id(self, recommender_with_mocks):
        """Test similar recipes with invalid recipe ID."""
        recommender = recommender_with_mocks
        
        similar_recipes = recommender.get_similar_recipes(recipe_id=999, top_n=2)
        
        # Should return empty list
        assert similar_recipes == []
    
    def test_benchmark_performance(self, recommender_with_mocks):
        """Test performance benchmarking."""
        recommender = recommender_with_mocks
        
        test_ingredients = ["chicken", "garlic", "onion"]
        metrics = recommender.benchmark_performance(test_ingredients, num_runs=2)
        
        # Should return performance metrics
        assert 'embedding_time_ms' in metrics
        assert 'search_time_ms' in metrics
        assert 'total_time_ms' in metrics
        assert 'num_recipes' in metrics
        assert 'embedding_dimension' in metrics
        
        # All times should be positive
        assert metrics['embedding_time_ms'] >= 0
        assert metrics['search_time_ms'] >= 0
        assert metrics['total_time_ms'] >= 0
    
    def test_get_model_info(self, recommender_with_mocks):
        """Test model information retrieval."""
        recommender = recommender_with_mocks
        
        # Before loading
        info = recommender.get_model_info()
        assert info['model_type'] == 'Embedding (Sentence-BERT + FAISS)'
        assert not info['is_loaded']
        
        # After loading
        recommender.load_models()
        info = recommender.get_model_info()
        assert info['is_loaded']
        assert 'num_recipes' in info
        assert 'embedding_dimension' in info
        assert 'model_name' in info
    
    @patch('recommender_embed.faiss')
    def test_load_models_failure(self, mock_faiss, mock_models_dir):
        """Test model loading failure handling."""
        # Mock faiss to raise an exception
        mock_faiss.normalize_L2.side_effect = Exception("FAISS error")
        
        recommender = EmbeddingRecommender(mock_models_dir)
        
        # Mock the model loader to raise an exception
        mock_loader = Mock()
        mock_loader.load_all_embedding_components.side_effect = Exception("Load error")
        recommender.model_loader = mock_loader
        
        with pytest.raises(Exception, match="Load error"):
            recommender.load_models()
        
        assert not recommender._is_loaded


class TestGlobalRecommender:
    """Test the global recommender instance."""
    
    def test_get_embedding_recommender(self):
        """Test getting the global recommender instance."""
        # Clear any existing instance
        import recommender_embed
        recommender_embed._embedding_recommender = None
        
        # Get instance
        recommender1 = get_embedding_recommender("test_dir")
        recommender2 = get_embedding_recommender("test_dir")
        
        # Should be the same instance
        assert recommender1 is recommender2
        assert recommender1.models_dir == "test_dir"


if __name__ == "__main__":
    pytest.main([__file__])