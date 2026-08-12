"""
Unit tests for TF-IDF recommender service.
Tests recommendation accuracy, filtering, and edge cases.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from .recommender_tfidf import TFIDFRecommender, get_tfidf_recommender


class TestTFIDFRecommender:
    """Test cases for TFIDFRecommender class."""
    
    @pytest.fixture
    def mock_model_data(self):
        """Create mock model data for testing."""
        # Mock vectorizer
        mock_vectorizer = Mock()
        mock_vectorizer.vocabulary_ = {'chicken': 0, 'tomato': 1, 'garlic': 2, 'pasta': 3}
        mock_vectorizer.transform.return_value = np.array([[0.5, 0.3, 0.2, 0.0]])
        
        # Mock recipe vectors (4 recipes, 4 features)
        mock_vectors = np.array([
            [0.6, 0.4, 0.0, 0.0],  # Recipe 0: chicken, tomato
            [0.0, 0.5, 0.3, 0.2],  # Recipe 1: tomato, garlic, pasta
            [0.8, 0.0, 0.2, 0.0],  # Recipe 2: chicken, garlic
            [0.0, 0.0, 0.0, 1.0]   # Recipe 3: pasta only
        ])
        
        # Mock recipe metadata
        mock_metadata = [
            {
                'id': 0,
                'title': 'Chicken Tomato Stew',
                'ingredients_cleaned': 'chicken,tomato',
                'cuisine': 'Italian',
                'diet_types': 'Regular',
                'cooking_time': 30,
                'difficulty': 'Easy'
            },
            {
                'id': 1,
                'title': 'Garlic Pasta',
                'ingredients_cleaned': 'tomato,garlic,pasta',
                'cuisine': 'Italian',
                'diet_types': 'Vegetarian',
                'cooking_time': 20,
                'difficulty': 'Easy'
            },
            {
                'id': 2,
                'title': 'Chicken Garlic Stir Fry',
                'ingredients_cleaned': 'chicken,garlic',
                'cuisine': 'Chinese',
                'diet_types': 'Regular',
                'cooking_time': 15,
                'difficulty': 'Medium'
            },
            {
                'id': 3,
                'title': 'Simple Pasta',
                'ingredients_cleaned': 'pasta',
                'cuisine': 'Italian',
                'diet_types': 'Vegetarian',
                'cooking_time': 10,
                'difficulty': 'Easy'
            }
        ]
        
        return mock_vectorizer, mock_vectors, mock_metadata
    
    @pytest.fixture
    def recommender_with_mocks(self, mock_model_data):
        """Create recommender with mocked model data."""
        mock_vectorizer, mock_vectors, mock_metadata = mock_model_data
        
        recommender = TFIDFRecommender()
        recommender._vectorizer = mock_vectorizer
        recommender._recipe_vectors = mock_vectors
        recommender._recipe_metadata = mock_metadata
        recommender._is_loaded = True
        
        return recommender
    
    def test_initialization(self):
        """Test recommender initialization."""
        recommender = TFIDFRecommender("test_models")
        assert recommender.models_dir == "test_models"
        assert not recommender._is_loaded
        assert recommender._vectorizer is None
        assert recommender._recipe_vectors is None
        assert recommender._recipe_metadata is None
    
    def test_preprocess_ingredients(self, recommender_with_mocks):
        """Test ingredient preprocessing."""
        recommender = recommender_with_mocks
        
        # Test normal case
        ingredients = ["Chicken Breast", "  Tomato  ", "GARLIC"]
        result = recommender._preprocess_ingredients(ingredients)
        assert result == "chicken breast,tomato,garlic"
        
        # Test empty ingredients
        result = recommender._preprocess_ingredients([])
        assert result == ""
        
        # Test ingredients with empty strings
        ingredients = ["chicken", "", "  ", "tomato"]
        result = recommender._preprocess_ingredients(ingredients)
        assert result == "chicken,tomato"
    
    def test_compute_similarity_scores(self, recommender_with_mocks):
        """Test similarity score computation."""
        recommender = recommender_with_mocks
        
        ingredients = ["chicken", "tomato"]
        scores = recommender.compute_similarity_scores(ingredients)
        
        assert isinstance(scores, np.ndarray)
        assert len(scores) == 4  # Number of recipes
        assert all(0 <= score <= 1 for score in scores)
    
    def test_compute_similarity_scores_empty_ingredients(self, recommender_with_mocks):
        """Test similarity computation with empty ingredients."""
        recommender = recommender_with_mocks
        
        scores = recommender.compute_similarity_scores([])
        
        assert isinstance(scores, np.ndarray)
        assert len(scores) == 4
        assert all(score == 0 for score in scores)
    
    def test_get_top_recommendations_basic(self, recommender_with_mocks):
        """Test basic recommendation functionality."""
        recommender = recommender_with_mocks
        
        ingredients = ["chicken", "tomato"]
        recommendations = recommender.get_top_recommendations(ingredients, top_n=3)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
        
        # Check recommendation structure
        if recommendations:
            rec = recommendations[0]
            required_fields = [
                'recipe_id', 'title', 'ingredients', 'cuisine', 'diet_types',
                'cooking_time', 'difficulty', 'similarity_score', 'match_percentage'
            ]
            for field in required_fields:
                assert field in rec
            
            # Check that scores are sorted in descending order
            scores = [rec['similarity_score'] for rec in recommendations]
            assert scores == sorted(scores, reverse=True)
    
    def test_get_top_recommendations_with_filters(self, recommender_with_mocks):
        """Test recommendations with cuisine and diet filters."""
        recommender = recommender_with_mocks
        
        ingredients = ["pasta"]
        
        # Test cuisine filter
        recommendations = recommender.get_top_recommendations(
            ingredients, cuisine_filter="Italian"
        )
        for rec in recommendations:
            assert rec['cuisine'].lower() == "italian"
        
        # Test diet filter
        recommendations = recommender.get_top_recommendations(
            ingredients, diet_filter="Vegetarian"
        )
        for rec in recommendations:
            assert "vegetarian" in rec['diet_types'].lower()
    
    def test_get_top_recommendations_min_score(self, recommender_with_mocks):
        """Test recommendations with minimum score threshold."""
        recommender = recommender_with_mocks
        
        ingredients = ["chicken"]
        recommendations = recommender.get_top_recommendations(
            ingredients, min_score=0.5
        )
        
        for rec in recommendations:
            assert rec['similarity_score'] >= 0.5
    
    def test_get_recipe_by_id(self, recommender_with_mocks):
        """Test recipe lookup by ID."""
        recommender = recommender_with_mocks
        
        # Test existing recipe
        recipe = recommender.get_recipe_by_id(1)
        assert recipe is not None
        assert recipe['id'] == 1
        assert recipe['title'] == 'Garlic Pasta'
        
        # Test non-existing recipe
        recipe = recommender.get_recipe_by_id(999)
        assert recipe is None
    
    def test_get_similar_recipes(self, recommender_with_mocks):
        """Test finding similar recipes."""
        recommender = recommender_with_mocks
        
        # Test with existing recipe
        similar = recommender.get_similar_recipes(0, top_n=2)
        
        assert isinstance(similar, list)
        assert len(similar) <= 2
        
        # Should not include the original recipe
        recipe_ids = [rec['recipe_id'] for rec in similar]
        assert 0 not in recipe_ids
        
        # Test with non-existing recipe
        similar = recommender.get_similar_recipes(999)
        assert similar == []
    
    def test_get_model_info(self, recommender_with_mocks):
        """Test model information retrieval."""
        recommender = recommender_with_mocks
        
        info = recommender.get_model_info()
        
        assert info['model_type'] == 'TF-IDF'
        assert info['is_loaded'] is True
        assert info['num_recipes'] == 4
        assert info['vocabulary_size'] == 4
        assert info['vector_dimensions'] == 4
    
    def test_get_model_info_not_loaded(self):
        """Test model info when models are not loaded."""
        recommender = TFIDFRecommender()
        
        info = recommender.get_model_info()
        
        assert info['model_type'] == 'TF-IDF'
        assert info['is_loaded'] is False
        assert 'num_recipes' not in info
    
    def test_load_models_success(self, mock_model_data):
        """Test successful model loading."""
        mock_vectorizer, mock_vectors, mock_metadata = mock_model_data
        
        recommender = TFIDFRecommender()
        
        # Mock the model loader directly on the instance
        mock_loader = Mock()
        mock_loader.load_all_tfidf_components.return_value = (
            mock_vectorizer, mock_vectors, mock_metadata
        )
        recommender.model_loader = mock_loader
        
        recommender.load_models()
        
        assert recommender._is_loaded is True
        assert recommender._vectorizer == mock_vectorizer
        assert np.array_equal(recommender._recipe_vectors, mock_vectors)
        assert recommender._recipe_metadata == mock_metadata
    
    def test_load_models_failure(self):
        """Test model loading failure."""
        recommender = TFIDFRecommender()
        
        # Mock the model loader to raise an exception
        mock_loader = Mock()
        mock_loader.load_all_tfidf_components.side_effect = Exception("Load failed")
        recommender.model_loader = mock_loader
        
        with pytest.raises(Exception, match="Load failed"):
            recommender.load_models()
        
        assert recommender._is_loaded is False
    
    def test_load_models_idempotent(self, recommender_with_mocks):
        """Test that load_models is idempotent."""
        recommender = recommender_with_mocks
        original_vectorizer = recommender._vectorizer
        
        # Should not reload if already loaded
        recommender.load_models()
        
        assert recommender._vectorizer is original_vectorizer


class TestGlobalRecommender:
    """Test global recommender instance management."""
    
    def test_get_tfidf_recommender_singleton(self):
        """Test that get_tfidf_recommender returns singleton."""
        # Clear any existing global instance
        import recommender_tfidf as module
        module._tfidf_recommender = None
        
        recommender1 = get_tfidf_recommender()
        recommender2 = get_tfidf_recommender()
        
        assert recommender1 is recommender2
        assert isinstance(recommender1, TFIDFRecommender)
    
    def test_get_tfidf_recommender_with_models_dir(self):
        """Test recommender creation with custom models directory."""
        # Clear any existing global instance
        import recommender_tfidf as module
        module._tfidf_recommender = None
        
        # Create a new recommender directly since the global function doesn't accept models_dir
        recommender = TFIDFRecommender("custom_models")
        assert recommender.models_dir == "custom_models"


if __name__ == "__main__":
    pytest.main([__file__])