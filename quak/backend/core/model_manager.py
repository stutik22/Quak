"""
Model loading and management utilities for performance optimization.
"""
import os
import time
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import threading
import psutil

try:
    # Try relative imports first (when run as module)
    from .config import settings
    from .caching import cache_manager, model_cache
    from ..models.simple_recommender import get_simple_recommender
    from ..models.hybrid_recommender import HybridRecommender
except ImportError:
    # Fall back to absolute imports (when run directly)
    from core.config import settings
    from core.caching import cache_manager, model_cache
    from models.simple_recommender import get_simple_recommender
    from models.hybrid_recommender import HybridRecommender


logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model loading, caching, and memory optimization."""
    
    def __init__(self):
        """Initialize the model manager."""
        self.models: Dict[str, Any] = {}
        self.simple_recommender = None
        self.hybrid_recommender = None
        self.load_times: Dict[str, float] = {}
        self.memory_usage: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._loaded = False
        
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dictionary with memory usage information
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
                'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {}
    
    def check_memory_constraints(self) -> bool:
        """
        Check if memory usage is within acceptable limits.
        
        Returns:
            True if memory usage is acceptable, False otherwise
        """
        try:
            memory_info = self.get_memory_usage()
            max_memory_mb = settings.model_cache_size
            
            if memory_info.get('rss_mb', 0) > max_memory_mb:
                logger.warning(f"Memory usage ({memory_info['rss_mb']:.1f}MB) exceeds limit ({max_memory_mb}MB)")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking memory constraints: {e}")
            return True  # Default to allowing operation
    
    def load_models(self, force_reload: bool = False) -> Dict[str, bool]:
        """
        Load all required models with optimization.
        
        Args:
            force_reload: Whether to force reload even if models are already loaded
            
        Returns:
            Dictionary with model loading status
        """
        with self._lock:
            if self._loaded and not force_reload:
                return self.get_model_status()
            
            logger.info("Loading models...")
            start_time = time.time()
            
            status = {
                'simple_loaded': False,
                'tfidf_loaded': False,
                'embedding_loaded': False,
                'hybrid_loaded': False
            }
            
            try:
                # Initialize simple recommender
                self.simple_recommender = get_simple_recommender()
                status['simple_loaded'] = True
                logger.info("Simple recommender loaded successfully")
                
                # Initialize hybrid recommender (which loads TF-IDF and Embedding models)
                self.hybrid_recommender = HybridRecommender()
                
                # Check status of underlying models
                model_info = self.hybrid_recommender.get_model_info()
                status['tfidf_loaded'] = model_info.get('tfidf_available', False)
                status['embedding_loaded'] = model_info.get('embedding_available', False)
                status['hybrid_loaded'] = True
                
                self._loaded = True
                total_time = time.time() - start_time
                logger.info(f"Model loading completed in {total_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Error during model loading: {e}")
            
            return status
    
    def get_model_status(self) -> Dict[str, bool]:
        """
        Get current model loading status.
        
        Returns:
            Dictionary with model status
        """
        status = {
            'simple_loaded': self.simple_recommender is not None,
            'tfidf_loaded': False,
            'embedding_loaded': False,
            'hybrid_loaded': self.hybrid_recommender is not None,
            'manager_loaded': self._loaded
        }
        
        if self.hybrid_recommender:
            info = self.hybrid_recommender.get_model_info()
            status['tfidf_loaded'] = info.get('tfidf_available', False)
            status['embedding_loaded'] = info.get('embedding_available', False)
            
        return status
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get detailed model information.
        
        Returns:
            Dictionary with model information
        """
        status = self.get_model_status()
        memory_info = self.get_memory_usage()
        
        return {
            'status': status,
            'load_times': self.load_times,
            'memory_usage': memory_info,
            'cache_stats': cache_manager.get_stats(),
            'models_available': list(self.models.keys()),
            'hybrid_available': self.hybrid_recommender is not None
        }
    
    def get_recommender(self):
        """
        Get the best available recommender instance.
        
        Returns:
            Recommender instance (Hybrid if available, else Simple)
        """
        if not self._loaded:
            logger.warning("Models not loaded, attempting to load now...")
            self.load_models()
        
        if self.hybrid_recommender and self.hybrid_recommender.is_available():
            return self.hybrid_recommender
            
        return self.simple_recommender
    
    def unload_models(self) -> bool:
        """
        Unload models to free memory.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                self.models.clear()
                self.simple_recommender = None
                self.hybrid_recommender = None
                self.load_times.clear()
                self._loaded = False
                
                # Clear model cache
                cache_manager.clear()
                
                logger.info("Models unloaded successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error unloading models: {e}")
                return False
    
    def reload_models(self) -> Dict[str, bool]:
        """
        Reload all models.
        
        Returns:
            Dictionary with model loading status
        """
        logger.info("Reloading models...")
        self.unload_models()
        return self.load_models()
    
    def optimize_memory(self) -> Dict[str, Any]:
        """
        Perform memory optimization operations.
        
        Returns:
            Dictionary with optimization results
        """
        logger.info("Performing memory optimization...")
        
        results = {
            'cache_cleared': False,
            'memory_before': self.get_memory_usage(),
            'memory_after': {},
            'optimization_time': 0
        }
        
        start_time = time.time()
        
        try:
            # Clear caches
            cache_manager.clear()
            results['cache_cleared'] = True
            
            # Force garbage collection
            import gc
            gc.collect()
            
            results['memory_after'] = self.get_memory_usage()
            results['optimization_time'] = time.time() - start_time
            
            logger.info(f"Memory optimization completed in {results['optimization_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"Error during memory optimization: {e}")
        
        return results


# Global model manager instance
model_manager = ModelManager()