"""
Tests for filtering and ranking utilities.
"""
import pytest
import tempfile
import pickle
from pathlib import Path
from utils.filters import RecipeFilter


@pytest.fixture
def sample_metadata():
    """Create sample recipe metadata for testing."""
    return [
        {
            'id': 0,
            'title': 'Spaghetti Carbonara',
            'ingredients_cleaned': 'spaghetti,egg,bacon,parmesan cheese,black pepper',
            'cuisine': 'Italian',
            'diet_types': 'Regular',
            'cooking_time': 20,
            'difficulty': 'Medium'
        },
        {
            'id': 1,
            'title': 'Vegan Buddha Bowl',
            'ingredients_cleaned': 'quinoa,chickpea,avocado,spinach,cherry tomato',
            'cuisine': 'Other',
            'diet_types': 'Vegan,Gluten-Free',
            'cooking_time': 45,
            'difficulty': 'Easy'
        },
        {
            'id': 2,
            'title': 'Chicken Tikka Masala',
            'ingredients_cleaned': 'chicken,tomato,onion,garlic,ginger,cream',
            'cuisine': 'Indian',
            'diet_types': 'Regular',
            'cooking_time': 60,
            'difficulty': 'Hard'
        },
        {
            'id': 3,
            'title': 'Vegetarian Pizza',
            'ingredients_cleaned': 'pizza dough,tomato sauce,mozzarella,bell pepper,mushroom',
            'cuisine': 'Italian',
            'diet_types': 'Vegetarian',
            'cooking_time': 30,
            'difficulty': 'Medium'
        }
    ]


@pytest.fixture
def temp_metadata_file(sample_metadata):
    """Create a temporary metadata file for testing."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pkl') as f:
        pickle.dump(sample_metadata, f)
        return f.name


def test_recipe_filter_initialization(temp_metadata_file):
    """Test RecipeFilter initialization."""
    filter_obj = RecipeFilter(temp_metadata_file)
    
    assert len(filter_obj.recipes_metadata) == 4
    assert 'Italian' in filter_obj.available_cuisines
    assert 'Indian' in filter_obj.available_cuisines
    assert 'Vegan' in filter_obj.available_diets
    assert 'Vegetarian' in filter_obj.available_diets


def test_get_available_filters(temp_metadata_file):
    """Test getting available filter options."""
    filter_obj = RecipeFilter(temp_metadata_file)
    filters = filter_obj.get_available_filters()
    
    assert 'cuisines' in filters
    assert 'diets' in filters
    assert 'Italian' in filters['cuisines']
    assert 'Vegan' in filters['diets']


def test_filter_by_cuisine(temp_metadata_file):
    """Test filtering recipes by cuisine."""
    filter_obj = RecipeFilter(temp_metadata_file)
    
    # Test Italian cuisine filter
    italian_recipes = filter_obj.filter_recipes([0, 1, 2, 3], cuisine_filter='Italian')
    assert len(italian_recipes) == 2
    assert 0 in italian_recipes  # Spaghetti Carbonara
    assert 3 in italian_recipes  # Vegetarian Pizza
    
    # Test Indian cuisine filter
    indian_recipes = filter_obj.filter_recipes([0, 1, 2, 3], cuisine_filter='Indian')
    assert len(indian_recipes) == 1
    assert 2 in indian_recipes  # Chicken Tikka Masala


def test_filter_by_diet(temp_metadata_file):
    """Test filtering recipes by diet type."""
    filter_obj = RecipeFilter(temp_metadata_file)
    
    # Test Vegan diet filter
    vegan_recipes = filter_obj.filter_recipes([0, 1, 2, 3], diet_filter='Vegan')
    assert len(vegan_recipes) == 1
    assert 1 in vegan_recipes  # Vegan Buddha Bowl
    
    # Test Vegetarian diet filter
    vegetarian_recipes = filter_obj.filter_recipes([0, 1, 2, 3], diet_filter='Vegetarian')
    assert len(vegetarian_recipes) == 1
    assert 3 in vegetarian_recipes  # Vegetarian Pizza


def test_filter_by_both_cuisine_and_diet(temp_metadata_file):
    """Test filtering by both cuisine and diet."""
    filter_obj = RecipeFilter(temp_metadata_file)
    
    # Test Italian + Vegetarian
    filtered = filter_obj.filter_recipes([0, 1, 2, 3], cuisine_filter='Italian', diet_filter='Vegetarian')
    assert len(filtered) == 1
    assert 3 in filtered  # Vegetarian Pizza
    
    # Test combination that should return no results
    filtered = filter_obj.filter_recipes([0, 1, 2, 3], cuisine_filter='Indian', diet_filter='Vegan')
    assert len(filtered) == 0


def test_calculate_match_percentage(temp_metadata_file):
    """Test match percentage calculation."""
    filter_obj = RecipeFilter(temp_metadata_file)
    
    # Perfect match
    user_ingredients = ['spaghetti', 'egg', 'bacon', 'parmesan cheese', 'black pepper']
    recipe_ingredients = 'spaghetti,egg,bacon,parmesan cheese,black pepper'
    match = filter_obj.calculate_match_percentage(user_ingredients, recipe_ingredients)
    assert match == 1.0
    
    # Partial match
    user_ingredients = ['spaghetti', 'egg']
    match = filter_obj.calculate_match_percentage(user_ingredients, recipe_ingredients)
    assert match == 0.4  # 2 out of 5 ingredients
    
    # No match
    user_ingredients = ['rice', 'beans']
    match = filter_obj.calculate_match_percentage(user_ingredients, recipe_ingredients)
    assert match == 0.0


def test_rank_and_score_recipes(temp_metadata_file):
    """Test ranking and scoring of recipes."""
    filter_obj = RecipeFilter(temp_metadata_file)
    
    recipe_indices = [0, 1, 2]
    similarity_scores = [0.8, 0.6, 0.9]
    user_ingredients = ['spaghetti', 'egg']
    
    ranked = filter_obj.rank_and_score_recipes(
        recipe_indices, similarity_scores, user_ingredients, max_results=3
    )
    
    assert len(ranked) == 3
    # Should be sorted by similarity score (descending)
    assert ranked[0][0] == 2  # Index 2 has highest similarity (0.9)
    assert ranked[1][0] == 0  # Index 0 has second highest (0.8)
    assert ranked[2][0] == 1  # Index 1 has lowest (0.6)
    
    # Check that match percentages are calculated
    assert all(len(item) == 3 for item in ranked)


def test_get_recipe_details(temp_metadata_file):
    """Test getting recipe details."""
    filter_obj = RecipeFilter(temp_metadata_file)
    
    details = filter_obj.get_recipe_details(0)
    
    assert details['id'] == 0
    assert details['title'] == 'Spaghetti Carbonara'
    assert 'spaghetti' in details['ingredients']
    assert details['cuisine'] == 'Italian'
    assert details['cooking_time'] == 20


def test_paginate_results(temp_metadata_file):
    """Test result pagination."""
    filter_obj = RecipeFilter(temp_metadata_file)
    
    # Create sample results
    results = [(i, 0.8 - i*0.1, 0.5) for i in range(10)]
    
    # Test first page
    paginated, info = filter_obj.paginate_results(results, page=1, page_size=3)
    assert len(paginated) == 3
    assert info['current_page'] == 1
    assert info['total_pages'] == 4
    assert info['has_next'] is True
    assert info['has_previous'] is False
    
    # Test last page
    paginated, info = filter_obj.paginate_results(results, page=4, page_size=3)
    assert len(paginated) == 1  # Only 1 item on last page
    assert info['has_next'] is False
    assert info['has_previous'] is True


if __name__ == "__main__":
    pytest.main([__file__])