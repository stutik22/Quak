"""
Filtering and ranking utilities for recipe recommendations.
"""
import pickle
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path


class RecipeFilter:
    """Handles filtering and ranking of recipe recommendations."""
    
    def __init__(self, metadata_path: str = "models/recipe_metadata.pkl"):
        """
        Initialize the recipe filter with metadata.
        
        Args:
            metadata_path: Path to the recipe metadata pickle file
        """
        self.metadata_path = Path(metadata_path)
        self.recipes_metadata = self._load_metadata()
        self.available_cuisines = self._extract_cuisines()
        self.available_diets = self._extract_diets()
    
    def _load_metadata(self) -> List[Dict[str, Any]]:
        """Load recipe metadata from pickle file."""
        try:
            with open(self.metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            return metadata
        except FileNotFoundError:
            raise FileNotFoundError(f"Recipe metadata not found at {self.metadata_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load recipe metadata: {str(e)}")
    
    def _extract_cuisines(self) -> List[str]:
        """Extract unique cuisine types from metadata."""
        cuisines = set()
        for recipe in self.recipes_metadata:
            if recipe.get('cuisine'):
                cuisines.add(recipe['cuisine'])
        return sorted(list(cuisines))
    
    def _extract_diets(self) -> List[str]:
        """Extract unique diet types from metadata."""
        diets = set()
        for recipe in self.recipes_metadata:
            diet_types = recipe.get('diet_types', '')
            if diet_types:
                # Split multiple diet types (e.g., "Vegan,Gluten-Free")
                for diet in diet_types.split(','):
                    diet = diet.strip()
                    if diet and diet != 'Regular':
                        diets.add(diet)
        return sorted(list(diets))
    
    def get_available_filters(self) -> Dict[str, List[str]]:
        """
        Get available filter options.
        
        Returns:
            Dictionary with available cuisines and diets
        """
        return {
            "cuisines": self.available_cuisines,
            "diets": self.available_diets
        }
    
    def filter_recipes(
        self,
        recipe_indices: List[int],
        cuisine_filter: Optional[str] = None,
        diet_filter: Optional[str] = None
    ) -> List[int]:
        """
        Filter recipe indices based on cuisine and diet criteria.
        
        Args:
            recipe_indices: List of recipe indices to filter
            cuisine_filter: Cuisine type to filter by
            diet_filter: Diet type to filter by
            
        Returns:
            Filtered list of recipe indices
        """
        filtered_indices = []
        
        for idx in recipe_indices:
            if idx >= len(self.recipes_metadata):
                continue
                
            recipe = self.recipes_metadata[idx]
            
            # Apply cuisine filter
            if cuisine_filter:
                recipe_cuisine = recipe.get('cuisine', '').strip()
                if not recipe_cuisine or recipe_cuisine.lower() != cuisine_filter.lower():
                    continue
            
            # Apply diet filter
            if diet_filter:
                recipe_diets = recipe.get('diet_types', '').strip()
                if not recipe_diets:
                    continue
                
                # Check if the diet filter matches any of the recipe's diet types
                diet_list = [d.strip().lower() for d in recipe_diets.split(',')]
                if diet_filter.lower() not in diet_list:
                    continue
            
            filtered_indices.append(idx)
        
        return filtered_indices
    
    def calculate_match_percentage(
        self,
        user_ingredients: List[str],
        recipe_ingredients: str
    ) -> float:
        """
        Calculate match percentage between user ingredients and recipe ingredients.
        
        Args:
            user_ingredients: List of user's available ingredients
            recipe_ingredients: Comma-separated string of recipe ingredients
            
        Returns:
            Match percentage as float between 0 and 1
        """
        if not recipe_ingredients:
            return 0.0
        
        # Normalize ingredients for comparison
        user_set = set(ingredient.lower().strip() for ingredient in user_ingredients)
        recipe_list = [ingredient.lower().strip() for ingredient in recipe_ingredients.split(',')]
        recipe_set = set(recipe_list)
        
        if not recipe_set:
            return 0.0
        
        # Calculate intersection
        matches = user_set.intersection(recipe_set)
        match_percentage = len(matches) / len(recipe_set)
        
        return min(match_percentage, 1.0)
    
    def rank_and_score_recipes(
        self,
        recipe_indices: List[int],
        similarity_scores: List[float],
        user_ingredients: List[str],
        max_results: int = 10
    ) -> List[Tuple[int, float, float]]:
        """
        Rank recipes by similarity scores and calculate match percentages.
        
        Args:
            recipe_indices: List of recipe indices
            similarity_scores: Corresponding similarity scores
            user_ingredients: User's available ingredients
            max_results: Maximum number of results to return
            
        Returns:
            List of tuples (recipe_index, similarity_score, match_percentage)
            sorted by similarity score in descending order
        """
        if len(recipe_indices) != len(similarity_scores):
            raise ValueError("Recipe indices and similarity scores must have the same length")
        
        # Calculate match percentages and combine with similarity scores
        scored_recipes = []
        for idx, sim_score in zip(recipe_indices, similarity_scores):
            if idx >= len(self.recipes_metadata):
                continue
                
            recipe = self.recipes_metadata[idx]
            recipe_ingredients = recipe.get('ingredients_cleaned', '')
            
            match_percentage = self.calculate_match_percentage(
                user_ingredients, recipe_ingredients
            )
            
            scored_recipes.append((idx, sim_score, match_percentage))
        
        # Sort by similarity score (descending)
        scored_recipes.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N results
        return scored_recipes[:max_results]
    
    def get_recipe_details(self, recipe_index: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific recipe.
        
        Args:
            recipe_index: Index of the recipe
            
        Returns:
            Dictionary with recipe details
        """
        if recipe_index >= len(self.recipes_metadata):
            raise IndexError(f"Recipe index {recipe_index} out of range")
        
        recipe = self.recipes_metadata[recipe_index]
        
        # Parse ingredients into list
        ingredients_str = recipe.get('ingredients_cleaned', '')
        ingredients_list = [ing.strip() for ing in ingredients_str.split(',') if ing.strip()]
        
        return {
            'id': recipe.get('id', recipe_index),
            'title': recipe.get('title', 'Unknown Recipe'),
            'ingredients': ingredients_list,
            'cuisine': recipe.get('cuisine'),
            'diet': recipe.get('diet_types'),
            'cooking_time': recipe.get('cooking_time'),
            'difficulty': recipe.get('difficulty')
        }
    
    def paginate_results(
        self,
        results: List[Tuple[int, float, float]],
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Tuple[int, float, float]], Dict[str, Any]]:
        """
        Paginate recipe results.
        
        Args:
            results: List of (recipe_index, similarity_score, match_percentage) tuples
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Tuple of (paginated_results, pagination_info)
        """
        total_results = len(results)
        total_pages = (total_results + page_size - 1) // page_size
        
        if page < 1:
            page = 1
        elif page > total_pages and total_pages > 0:
            page = total_pages
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_results = results[start_idx:end_idx]
        
        pagination_info = {
            'current_page': page,
            'page_size': page_size,
            'total_results': total_results,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }
        
        return paginated_results, pagination_info