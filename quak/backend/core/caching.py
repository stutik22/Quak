"""
Caching utilities for performance optimization.
"""
import json
import hashlib
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import redis
from redis.exceptions import ConnectionError, RedisError

try:
    # Try relative imports first (when run as module)
    from .config import settings
except ImportError:
    # Fall back to absolute imports (when run directly)
    from core.config import settings


logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching operations with Redis backend and fallback to in-memory cache."""
    
    def __init__(self, redis_url: Optional[str] = None, enable_redis: bool = True):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
            enable_redis: Whether to enable Redis caching
        """
        self.redis_client = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.enable_redis = enable_redis
        
        if enable_redis:
            self._init_redis(redis_url)
    
    def _init_redis(self, redis_url: Optional[str] = None):
        """Initialize Redis connection."""
        try:
            if redis_url:
                self.redis_client = redis.from_url(redis_url)
            else:
                # Try to connect to local Redis
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
            
        except (ConnectionError, RedisError) as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to memory cache.")
            self.redis_client = None
        except Exception as e:
            logger.warning(f"Unexpected error initializing Redis: {e}. Falling back to memory cache.")
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, data: Any) -> str:
        """
        Generate a cache key from data.
        
        Args:
            prefix: Key prefix
            data: Data to hash for the key
            
        Returns:
            Cache key string
        """
        # Convert data to string for hashing
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Create hash
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            # Try Redis first
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            
            # Fall back to memory cache
            if key in self.memory_cache:
                cache_entry = self.memory_cache[key]
                # Check expiration
                if cache_entry['expires_at'] > datetime.now():
                    return cache_entry['value']
                else:
                    # Remove expired entry
                    del self.memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized_value = json.dumps(value)
            
            # Try Redis first
            if self.redis_client:
                return self.redis_client.setex(key, ttl, serialized_value)
            
            # Fall back to memory cache
            expires_at = datetime.now() + timedelta(seconds=ttl)
            self.memory_cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
            
            # Clean up expired entries periodically
            self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = True
            
            # Delete from Redis
            if self.redis_client:
                self.redis_client.delete(key)
            
            # Delete from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear Redis
            if self.redis_client:
                self.redis_client.flushdb()
            
            # Clear memory cache
            self.memory_cache.clear()
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache."""
        try:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry['expires_at'] <= now
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
                
        except Exception as e:
            logger.error(f"Error cleaning up memory cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            'redis_available': self.redis_client is not None,
            'memory_cache_size': len(self.memory_cache)
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats.update({
                    'redis_used_memory': info.get('used_memory_human', 'unknown'),
                    'redis_connected_clients': info.get('connected_clients', 0),
                    'redis_keyspace_hits': info.get('keyspace_hits', 0),
                    'redis_keyspace_misses': info.get('keyspace_misses', 0)
                })
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")
        
        return stats


class RecommendationCache:
    """Specialized cache for recipe recommendations."""
    
    def __init__(self, cache_manager: CacheManager):
        """
        Initialize recommendation cache.
        
        Args:
            cache_manager: Cache manager instance
        """
        self.cache = cache_manager
        self.default_ttl = 3600  # 1 hour
    
    def get_recommendations(
        self,
        ingredients: List[str],
        cuisine_filter: Optional[str] = None,
        diet_filter: Optional[str] = None,
        max_results: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached recommendations.
        
        Args:
            ingredients: List of ingredients
            cuisine_filter: Cuisine filter
            diet_filter: Diet filter
            max_results: Maximum results
            
        Returns:
            Cached recommendations or None
        """
        cache_key = self.cache._generate_cache_key(
            "recommendations",
            {
                'ingredients': sorted(ingredients),
                'cuisine_filter': cuisine_filter,
                'diet_filter': diet_filter,
                'max_results': max_results
            }
        )
        
        return self.cache.get(cache_key)
    
    def set_recommendations(
        self,
        ingredients: List[str],
        cuisine_filter: Optional[str] = None,
        diet_filter: Optional[str] = None,
        max_results: int = 10,
        recommendations: Dict[str, Any] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache recommendations.
        
        Args:
            ingredients: List of ingredients
            cuisine_filter: Cuisine filter
            diet_filter: Diet filter
            max_results: Maximum results
            recommendations: Recommendations to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self.cache._generate_cache_key(
            "recommendations",
            {
                'ingredients': sorted(ingredients),
                'cuisine_filter': cuisine_filter,
                'diet_filter': diet_filter,
                'max_results': max_results
            }
        )
        
        return self.cache.set(cache_key, recommendations, ttl or self.default_ttl)


class ModelCache:
    """Cache for ML models and their outputs."""
    
    def __init__(self, cache_manager: CacheManager):
        """
        Initialize model cache.
        
        Args:
            cache_manager: Cache manager instance
        """
        self.cache = cache_manager
        self.model_ttl = 86400  # 24 hours for model outputs
    
    def get_model_predictions(self, model_name: str, input_hash: str) -> Optional[Any]:
        """
        Get cached model predictions.
        
        Args:
            model_name: Name of the model
            input_hash: Hash of the input data
            
        Returns:
            Cached predictions or None
        """
        cache_key = f"model:{model_name}:{input_hash}"
        return self.cache.get(cache_key)
    
    def set_model_predictions(
        self,
        model_name: str,
        input_hash: str,
        predictions: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache model predictions.
        
        Args:
            model_name: Name of the model
            input_hash: Hash of the input data
            predictions: Predictions to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = f"model:{model_name}:{input_hash}"
        return self.cache.set(cache_key, predictions, ttl or self.model_ttl)


# Global cache instances
cache_manager = CacheManager(enable_redis=getattr(settings, 'enable_redis_cache', True))
recommendation_cache = RecommendationCache(cache_manager)
model_cache = ModelCache(cache_manager)