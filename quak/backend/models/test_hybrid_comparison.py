"""
Test comparing TF-IDF and Embedding recommenders side by side.
"""

import pytest
from recommender_tfidf import get_tfidf_recommender
from recommender_embed import get_embedding_recommender


def test_both_recommenders():
    """Test that both recommenders work and produce different results."""
    # Get both recommenders
    tfidf_rec = get_tfidf_recommender(".")
    embed_rec = get_embedding_recommender(".")
    
    # Load models
    tfidf_rec.load_models()
    embed_rec.load_models()
    
    # Test ingredients
    ingredients = ["chicken", "garlic", "onion"]
    
    # Get recommendations from both
    tfidf_recs = tfidf_rec.get_top_recommendations(ingredients, top_n=3)
    embed_recs = embed_rec.get_top_recommendations(ingredients, top_n=3)
    
    # Both should return recommendations
    assert len(tfidf_recs) > 0
    assert len(embed_recs) > 0
    
    print(f"\nTF-IDF Recommendations for {ingredients}:")
    for i, rec in enumerate(tfidf_recs):
        print(f"{i+1}. {rec['title']} (Score: {rec['similarity_score']:.4f})")
    
    print(f"\nEmbedding Recommendations for {ingredients}:")
    for i, rec in enumerate(embed_recs):
        print(f"{i+1}. {rec['title']} (Score: {rec['similarity_score']:.4f})")
    
    # Get model info
    tfidf_info = tfidf_rec.get_model_info()
    embed_info = embed_rec.get_model_info()
    
    print(f"\nTF-IDF Model: {tfidf_info['model_type']}")
    print(f"Embedding Model: {embed_info['model_type']}")
    
    # Both should be loaded and have same number of recipes
    assert tfidf_info['is_loaded']
    assert embed_info['is_loaded']
    assert tfidf_info['num_recipes'] == embed_info['num_recipes']


if __name__ == "__main__":
    test_both_recommenders()