"""
Integration test for TF-IDF recommender with real model files.
"""

from recommender_tfidf import TFIDFRecommender

def test_real_model_integration():
    """Test the recommender with actual model files."""
    recommender = TFIDFRecommender(".")
    
    try:
        # Load the models
        recommender.load_models()
        print("✓ Models loaded successfully")
        
        # Test basic recommendation
        ingredients = ["chicken", "tomato", "garlic"]
        recommendations = recommender.get_top_recommendations(ingredients, top_n=3)
        
        print(f"✓ Generated {len(recommendations)} recommendations for {ingredients}")
        
        for i, rec in enumerate(recommendations):
            print(f"  {i+1}. {rec['title']} (Score: {rec['similarity_score']:.3f})")
            print(f"     Ingredients: {rec['ingredients']}")
            print(f"     Cuisine: {rec['cuisine']}, Diet: {rec['diet_types']}")
        
        # Test with filters
        filtered_recs = recommender.get_top_recommendations(
            ingredients, 
            cuisine_filter="Italian",
            top_n=2
        )
        print(f"✓ Generated {len(filtered_recs)} Italian recommendations")
        
        # Test model info
        info = recommender.get_model_info()
        print(f"✓ Model info: {info['num_recipes']} recipes, {info['vocabulary_size']} vocabulary")
        
        print("\n🎉 Integration test passed!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        raise

if __name__ == "__main__":
    test_real_model_integration()