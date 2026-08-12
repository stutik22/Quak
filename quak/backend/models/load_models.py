"""
Model loading utilities for the recipe recommendation system.
Handles loading of TF-IDF vectorizer, recipe vectors, and metadata.
"""

import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import faiss
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class ModelLoader:
    """Handles loading and caching of ML models and data."""
    
    def __init__(self, models_dir: str = "models"):
        """
        Initialize the model loader.
        
        Args:
            models_dir: Directory containing model files
        """
        self.models_dir = Path(models_dir)
        self._vectorizer = None
        self._tfidf_vectors = None
        self._recipe_metadata = None
        self._embedding_model = None
        self._embedding_vectors = None
        self._faiss_index = None
        self._embedding_metadata = None
        
    def load_tfidf_vectorizer(self) -> Any:
        """
        Load the trained TF-IDF vectorizer.
        
        Returns:
            Trained TfidfVectorizer instance
            
        Raises:
            FileNotFoundError: If vectorizer file doesn't exist
            Exception: If loading fails
        """
        if self._vectorizer is not None:
            return self._vectorizer
            
        vectorizer_path = self.models_dir / "vectorizer.pkl"
        
        if not vectorizer_path.exists():
            raise FileNotFoundError(f"Vectorizer not found at {vectorizer_path}")
            
        try:
            with open(vectorizer_path, 'rb') as f:
                self._vectorizer = pickle.load(f)
            logger.info(f"Loaded TF-IDF vectorizer from {vectorizer_path}")
            return self._vectorizer
        except Exception as e:
            logger.error(f"Failed to load vectorizer: {e}")
            raise
    
    def load_tfidf_vectors(self) -> np.ndarray:
        """
        Load the pre-computed TF-IDF vectors for all recipes.
        
        Returns:
            NumPy array of TF-IDF vectors
            
        Raises:
            FileNotFoundError: If vectors file doesn't exist
            Exception: If loading fails
        """
        if self._tfidf_vectors is not None:
            return self._tfidf_vectors
            
        vectors_path = self.models_dir / "recipe_vectors_tfidf.npz"
        
        if not vectors_path.exists():
            raise FileNotFoundError(f"TF-IDF vectors not found at {vectors_path}")
            
        try:
            data = np.load(vectors_path)
            self._tfidf_vectors = data['vectors']
            logger.info(f"Loaded TF-IDF vectors from {vectors_path}, shape: {self._tfidf_vectors.shape}")
            return self._tfidf_vectors
        except Exception as e:
            logger.error(f"Failed to load TF-IDF vectors: {e}")
            raise
    
    def load_recipe_metadata(self) -> List[Dict[str, Any]]:
        """
        Load recipe metadata for quick lookup.
        
        Returns:
            List of recipe metadata dictionaries
            
        Raises:
            FileNotFoundError: If metadata file doesn't exist
            Exception: If loading fails
        """
        if self._recipe_metadata is not None:
            return self._recipe_metadata
            
        metadata_path = self.models_dir / "recipe_metadata.pkl"
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"Recipe metadata not found at {metadata_path}")
            
        try:
            with open(metadata_path, 'rb') as f:
                self._recipe_metadata = pickle.load(f)
            logger.info(f"Loaded metadata for {len(self._recipe_metadata)} recipes")
            return self._recipe_metadata
        except Exception as e:
            logger.error(f"Failed to load recipe metadata: {e}")
            raise
    
    def load_all_tfidf_components(self) -> Tuple[Any, np.ndarray, List[Dict[str, Any]]]:
        """
        Load all TF-IDF model components at once.
        
        Returns:
            Tuple of (vectorizer, tfidf_vectors, recipe_metadata)
        """
        vectorizer = self.load_tfidf_vectorizer()
        vectors = self.load_tfidf_vectors()
        metadata = self.load_recipe_metadata()
        
        return vectorizer, vectors, metadata
    
    def load_embedding_model(self) -> SentenceTransformer:
        """
        Load the Sentence-BERT embedding model.
        
        Returns:
            SentenceTransformer model instance
            
        Raises:
            Exception: If loading fails
        """
        if self._embedding_model is not None:
            return self._embedding_model
            
        try:
            # Load the same model used for training
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded Sentence-BERT embedding model (all-MiniLM-L6-v2)")
            return self._embedding_model
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def load_embedding_vectors(self) -> np.ndarray:
        """
        Load the pre-computed embedding vectors for all recipes.
        
        Returns:
            NumPy array of embedding vectors
            
        Raises:
            FileNotFoundError: If vectors file doesn't exist
            Exception: If loading fails
        """
        if self._embedding_vectors is not None:
            return self._embedding_vectors
            
        vectors_path = self.models_dir / "recipe_vectors_embed.npy"
        
        if not vectors_path.exists():
            raise FileNotFoundError(f"Embedding vectors not found at {vectors_path}")
            
        try:
            self._embedding_vectors = np.load(vectors_path)
            logger.info(f"Loaded embedding vectors from {vectors_path}, shape: {self._embedding_vectors.shape}")
            return self._embedding_vectors
        except Exception as e:
            logger.error(f"Failed to load embedding vectors: {e}")
            raise
    
    def load_faiss_index(self) -> faiss.Index:
        """
        Load the FAISS index for efficient similarity search.
        
        Returns:
            FAISS index instance
            
        Raises:
            FileNotFoundError: If index file doesn't exist
            Exception: If loading fails
        """
        if self._faiss_index is not None:
            return self._faiss_index
            
        index_path = self.models_dir / "recipe_faiss_index.bin"
        
        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not found at {index_path}")
            
        try:
            self._faiss_index = faiss.read_index(str(index_path))
            logger.info(f"Loaded FAISS index from {index_path}, {self._faiss_index.ntotal} vectors")
            return self._faiss_index
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            raise
    
    def load_embedding_metadata(self) -> Dict[str, Any]:
        """
        Load embedding model metadata.
        
        Returns:
            Dictionary with embedding metadata
            
        Raises:
            FileNotFoundError: If metadata file doesn't exist
            Exception: If loading fails
        """
        if self._embedding_metadata is not None:
            return self._embedding_metadata
            
        metadata_path = self.models_dir / "embedding_metadata.pkl"
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"Embedding metadata not found at {metadata_path}")
            
        try:
            with open(metadata_path, 'rb') as f:
                self._embedding_metadata = pickle.load(f)
            logger.info(f"Loaded embedding metadata: {self._embedding_metadata}")
            return self._embedding_metadata
        except Exception as e:
            logger.error(f"Failed to load embedding metadata: {e}")
            raise
    
    def load_all_embedding_components(self) -> Tuple[SentenceTransformer, np.ndarray, faiss.Index, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Load all embedding model components at once.
        
        Returns:
            Tuple of (embedding_model, embedding_vectors, faiss_index, recipe_metadata, embedding_metadata)
        """
        embedding_model = self.load_embedding_model()
        embedding_vectors = self.load_embedding_vectors()
        faiss_index = self.load_faiss_index()
        recipe_metadata = self.load_recipe_metadata()
        embedding_metadata = self.load_embedding_metadata()
        
        return embedding_model, embedding_vectors, faiss_index, recipe_metadata, embedding_metadata
    
    def clear_cache(self):
        """Clear all cached models to free memory."""
        self._vectorizer = None
        self._tfidf_vectors = None
        self._recipe_metadata = None
        self._embedding_model = None
        self._embedding_vectors = None
        self._faiss_index = None
        self._embedding_metadata = None
        logger.info("Cleared model cache")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about loaded models.
        
        Returns:
            Dictionary with model information
        """
        info = {
            "vectorizer_loaded": self._vectorizer is not None,
            "tfidf_vectors_loaded": self._tfidf_vectors is not None,
            "embedding_model_loaded": self._embedding_model is not None,
            "embedding_vectors_loaded": self._embedding_vectors is not None,
            "faiss_index_loaded": self._faiss_index is not None,
            "metadata_loaded": self._recipe_metadata is not None,
            "models_dir": str(self.models_dir)
        }
        
        if self._tfidf_vectors is not None:
            info["tfidf_vector_shape"] = self._tfidf_vectors.shape
            info["num_recipes"] = self._tfidf_vectors.shape[0]
            
        if self._embedding_vectors is not None:
            info["embedding_vector_shape"] = self._embedding_vectors.shape
            info["embedding_dimension"] = self._embedding_vectors.shape[1]
            
        if self._vectorizer is not None:
            info["vocabulary_size"] = len(self._vectorizer.vocabulary_)
            
        if self._faiss_index is not None:
            info["faiss_index_size"] = self._faiss_index.ntotal
            
        if self._recipe_metadata is not None:
            info["metadata_count"] = len(self._recipe_metadata)
            
        return info


# Global model loader instance
_model_loader = None

def get_model_loader(models_dir: str = "models") -> ModelLoader:
    """
    Get the global model loader instance.
    
    Args:
        models_dir: Directory containing model files
        
    Returns:
        ModelLoader instance
    """
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader(models_dir)
    return _model_loader


def load_tfidf_components(models_dir: str = "models") -> Tuple[Any, np.ndarray, List[Dict[str, Any]]]:
    """
    Convenience function to load all TF-IDF components.
    
    Args:
        models_dir: Directory containing model files
        
    Returns:
        Tuple of (vectorizer, tfidf_vectors, recipe_metadata)
    """
    loader = get_model_loader(models_dir)
    return loader.load_all_tfidf_components()


def load_embedding_components(models_dir: str = "models") -> Tuple[SentenceTransformer, np.ndarray, faiss.Index, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function to load all embedding components.
    
    Args:
        models_dir: Directory containing model files
        
    Returns:
        Tuple of (embedding_model, embedding_vectors, faiss_index, recipe_metadata, embedding_metadata)
    """
    loader = get_model_loader(models_dir)
    return loader.load_all_embedding_components()