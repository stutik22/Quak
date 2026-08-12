"""
Text cleaning utilities for recipe ingredient processing.
"""
import re
import string
from typing import List, Set
from nltk.stem import WordNetLemmatizer
import nltk
import pandas as pd

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class TextCleaner:
    """Handles text cleaning and normalization for recipe ingredients."""
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_ingredients = self._load_stop_ingredients()
        self.measurement_words = self._load_measurement_words()
    
    def _load_stop_ingredients(self) -> Set[str]:
        """Load common stop ingredients that don't add value to recommendations."""
        return {
            'water', 'salt', 'oil', 'butter', 'sugar', 'flour',
            'black pepper', 'white pepper', 'olive oil', 'vegetable oil',
            'kosher salt', 'sea salt', 'table salt', 'all-purpose flour',
            'granulated sugar', 'white sugar', 'brown sugar', 'vanilla',
            'vanilla extract', 'baking powder', 'baking soda', 'cornstarch'
        }
    
    def _load_measurement_words(self) -> Set[str]:
        """Load common measurement and quantity words to filter out."""
        return {
            # Quantities
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
            'half', 'quarter', 'third', 'whole', 'large', 'small', 'medium',
            
            # Measurements
            'cup', 'cups', 'tbsp', 'tsp', 'tablespoon', 'tablespoons', 
            'teaspoon', 'teaspoons', 'oz', 'ounce', 'ounces', 'lb', 'lbs',
            'pound', 'pounds', 'gram', 'grams', 'kg', 'kilogram', 'kilograms',
            'ml', 'milliliter', 'milliliters', 'liter', 'liters', 'pint', 'pints',
            'quart', 'quarts', 'gallon', 'gallons', 'inch', 'inches',
            'clove', 'cloves',
            
            # Preparation words
            'chopped', 'diced', 'sliced', 'minced', 'crushed', 'grated',
            'fresh', 'dried', 'frozen', 'canned', 'cooked', 'raw',
            'to', 'taste', 'and', 'or', 'of', 'for', 'with', 'without'
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text by converting to lowercase and removing punctuation.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def singularize_word(self, word: str) -> str:
        """
        Convert plural words to singular using lemmatization.
        
        Args:
            word: Word to singularize
            
        Returns:
            Singular form of the word
        """
        return self.lemmatizer.lemmatize(word.lower())
    
    def process_ingredients(self, ingredients: List[str]) -> List[str]:
        """
        Process a list of ingredients by cleaning, singularizing, and filtering.
        
        Args:
            ingredients: List of raw ingredient strings
            
        Returns:
            List of processed ingredient strings
        """
        processed = []
        
        for ingredient in ingredients:
            # Clean the text
            cleaned = self.clean_text(ingredient)
            
            if not cleaned:
                continue
            
            # Split into words and process each
            words = cleaned.split()
            processed_words = []
            
            for word in words:
                # Singularize the word
                singular = self.singularize_word(word)
                
                # Skip stop ingredients, measurement words, and very short words
                if (singular not in self.stop_ingredients and 
                    singular not in self.measurement_words and 
                    len(singular) > 2):
                    processed_words.append(singular)
            
            # Join processed words back together
            if processed_words:
                processed_ingredient = ' '.join(processed_words)
                processed.append(processed_ingredient)
        
        return processed
    
    def clean_ingredient_list(self, ingredient_string: str) -> List[str]:
        """
        Clean a comma-separated ingredient string into a list of processed ingredients.
        
        Args:
            ingredient_string: Comma-separated string of ingredients
            
        Returns:
            List of cleaned ingredient strings
        """
        if not ingredient_string:
            return []
        
        # Split by common separators
        ingredients = re.split(r'[,;|\n]', ingredient_string)
        
        # Clean each ingredient
        ingredients = [self.clean_text(ing.strip()) for ing in ingredients if ing.strip()]
        
        # Process the ingredients
        return self.process_ingredients(ingredients)


def clean_recipe_data(recipes_df):
    """
    Clean recipe dataframe with text processing.
    
    Args:
        recipes_df: Pandas DataFrame with recipe data
        
    Returns:
        Cleaned DataFrame
    """
    cleaner = TextCleaner()
    
    # Clean ingredient lists
    if 'ingredients' in recipes_df.columns:
        recipes_df['ingredients_cleaned'] = recipes_df['ingredients'].apply(
            lambda x: cleaner.clean_ingredient_list(str(x)) if pd.notna(x) else []
        )
    
    # Clean recipe titles
    if 'title' in recipes_df.columns:
        recipes_df['title_cleaned'] = recipes_df['title'].apply(
            lambda x: cleaner.clean_text(str(x)) if pd.notna(x) else ""
        )
    
    return recipes_df