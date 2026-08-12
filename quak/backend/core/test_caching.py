"""
Tests for caching functionality.
"""
import pytest
import time
from unittest.mock import Mock, patch
from core.caching import CacheManager, RecommendationCache, ModelCache


@pytest.fixture
def cache_manager():
    """Create a cache manager for testing (without Redis)."""
    return CacheManager(enable_redis=False)


def test_cache_manager_initialization():
    """Test cache manager initialization."""
    # Test with Redis disabled
    cache = CacheManager(enable_redis=False)
    assert cache.redis_client is None
    assert isinstance(cache.memory_cache, dict)
    
    # Test with Redis enabled but no connection
    with patch('redis.Redis') as mock_redis:
        mock_redis.return_value.ping.side_effect = Exception("Connection failed")
        cache = CacheManager(enable_redis=True)
        assert cache.redis_client is None


def test_memory_cache_operations(cache_manager):
    """Test basic cache operations with memory cache."""
    # Test set and get
    key = "test_key"
    value = {"data": "test_value", "number": 42}
    
    success = cache_manager.set(key, value, ttl=60)
    assert success is True
    
    retrieved = cache_manager.get(key)
    assert retrieved == value
    
    # Test non-existent key
    assert cache_manager.get("non_existent") is None


def test_cache_expiration(cache_manager):
    """Test cache expiration."""
    key = "expiring_key"
    value = "expiring_value"
    
    # Set with very short TTL
    cache_manager.set(key, value, ttl=1)
    
    # Should be available immediately
    assert cache_manager.get(key) == value
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Should be expired
    assert cache_manager.get(key) is None


def test_cache_delete(cache_manager):
    """Test cache deletion."""
    key = "delete_key"
    value = "delete_value"
    
    cache_manager.set(key, value)
    assert cache_manager.get(key) == value
    
    success = cache_manager.delete(key)
    assert success is True
    assert cache_manager.get(key) is None


def test_cache_clear(cache_manager):
    """Test cache clearing."""
    # Set multiple keys
    cache_manager.set("key1", "value1")
    cache_manager.set("key2", "value2")
    
    assert cache_manager.get("key1") == "value1"
    assert cache_manager.get("key2") == "value2"
    
    # Clear cache
    success = cache_manager.clear()
    assert success is True
    
    assert cache_manager.get("key1") is None
    assert cache_manager.get("key2") is None


def test_cache_key_generation(cache_manager):
    """Test cache key generation."""
    # Test with different data types
    key1 = cache_manager._generate_cache_key("prefix", {"a": 1, "b": 2})
    key2 = cache_manager._generate_cache_key("prefix", {"b": 2, "a": 1})  # Same data, different order
    key3 = cache_manager._generate_cache_key("prefix", {"a": 1, "b": 3})  # Different data
    
    # Same data should generate same key regardless of order
    assert key1 == key2
    
    # Different data should generate different keys
    assert key1 != key3


def test_cache_stats(cache_manager):
    """Test cache statistics."""
    stats = cache_manager.get_stats()
    
    assert 'redis_available' in stats
    assert 'memory_cache_size' in stats
    assert stats['redis_available'] is False  # Redis disabled in test
    
    # Add some data and check stats
    cache_manager.set("test", "value")
    stats = cache_manager.get_stats()
    assert stats['memory_cache_size'] >= 1


def test_recommendation_cache():
    """Test recommendation cache functionality."""
    cache_manager = CacheManager(enable_redis=False)
    rec_cache = RecommendationCache(cache_manager)
    
    ingredients = ["tomato", "cheese", "pasta"]
    cuisine_filter = "Italian"
    diet_filter = None
    max_results = 10
    
    # Test cache miss
    result = rec_cache.get_recommendations(
        ingredients, cuisine_filter, diet_filter, max_results
    )
    assert result is None
    
    # Set cache
    recommendations = {
        "recipes": [{"id": 1, "title": "Test Recipe"}],
        "total_found": 1
    }
    
    success = rec_cache.set_recommendations(
        ingredients, cuisine_filter, diet_filter, max_results, recommendations
    )
    assert success is True
    
    # Test cache hit
    result = rec_cache.get_recommendations(
        ingredients, cuisine_filter, diet_filter, max_results
    )
    assert result == recommendations


def test_model_cache():
    """Test model cache functionality."""
    cache_manager = CacheManager(enable_redis=False)
    model_cache = ModelCache(cache_manager)
    
    model_name = "test_model"
    input_hash = "abc123"
    predictions = [0.8, 0.6, 0.9]
    
    # Test cache miss
    result = model_cache.get_model_predictions(model_name, input_hash)
    assert result is None
    
    # Set cache
    success = model_cache.set_model_predictions(model_name, input_hash, predictions)
    assert success is True
    
    # Test cache hit
    result = model_cache.get_model_predictions(model_name, input_hash)
    assert result == predictions


def test_cache_error_handling():
    """Test cache error handling."""
    cache_manager = CacheManager(enable_redis=False)
    
    # Test with invalid JSON serialization
    with patch('json.dumps', side_effect=Exception("Serialization error")):
        success = cache_manager.set("key", "value")
        assert success is False
    
    # Test with invalid JSON deserialization
    cache_manager.memory_cache["test_key"] = {
        'value': "invalid_json",
        'expires_at': time.time() + 3600
    }
    
    with patch('json.loads', side_effect=Exception("Deserialization error")):
        result = cache_manager.get("test_key")
        assert result is None


def test_cache_cleanup():
    """Test cache cleanup functionality."""
    cache_manager = CacheManager(enable_redis=False)
    
    # Add expired entries
    cache_manager.set("key1", "value1", ttl=1)
    cache_manager.set("key2", "value2", ttl=60)
    
    # Wait for first key to expire
    time.sleep(1.1)
    
    # Trigger cleanup by setting a new key
    cache_manager.set("key3", "value3")
    
    # Check that expired key is cleaned up
    assert cache_manager.get("key1") is None
    assert cache_manager.get("key2") == "value2"
    assert cache_manager.get("key3") == "value3"


if __name__ == "__main__":
    pytest.main([__file__])