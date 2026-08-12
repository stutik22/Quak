"""
Unit tests for text cleaning functionality.
"""
import unittest
from text_cleaner import TextCleaner


class TestTextCleaner(unittest.TestCase):
    """Test cases for TextCleaner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cleaner = TextCleaner()
    
    def test_clean_text_basic(self):
        """Test basic text cleaning functionality."""
        # Test lowercase conversion
        result = self.cleaner.clean_text("TOMATOES")
        self.assertEqual(result, "tomatoes")
        
        # Test punctuation removal
        result = self.cleaner.clean_text("tomatoes, onions & garlic!")
        self.assertEqual(result, "tomatoes onions garlic")
        
        # Test whitespace normalization
        result = self.cleaner.clean_text("  tomatoes   onions  ")
        self.assertEqual(result, "tomatoes onions")
    
    def test_clean_text_edge_cases(self):
        """Test edge cases for text cleaning."""
        # Empty string
        result = self.cleaner.clean_text("")
        self.assertEqual(result, "")
        
        # None input
        result = self.cleaner.clean_text(None)
        self.assertEqual(result, "")
        
        # Only punctuation
        result = self.cleaner.clean_text("!@#$%")
        self.assertEqual(result, "")
    
    def test_singularize_word(self):
        """Test word singularization."""
        # Basic plurals
        self.assertEqual(self.cleaner.singularize_word("tomatoes"), "tomato")
        self.assertEqual(self.cleaner.singularize_word("onions"), "onion")
        self.assertEqual(self.cleaner.singularize_word("carrots"), "carrot")
        
        # Already singular
        self.assertEqual(self.cleaner.singularize_word("garlic"), "garlic")
        self.assertEqual(self.cleaner.singularize_word("rice"), "rice")
    
    def test_process_ingredients(self):
        """Test ingredient list processing."""
        ingredients = [
            "2 large tomatoes",
            "1 cup chopped onions", 
            "3 cloves garlic",
            "salt and pepper to taste",
            "2 tbsp olive oil"
        ]
        
        result = self.cleaner.process_ingredients(ingredients)
        
        # Should contain processed ingredients without measurement words and stop words
        self.assertIn("tomato", result)
        self.assertIn("onion", result)
        self.assertIn("garlic", result)
        
        # Should not contain stop ingredients
        self.assertNotIn("salt", " ".join(result))
        self.assertNotIn("olive oil", " ".join(result))
        
        # Should not contain measurement words
        result_text = " ".join(result)
        self.assertNotIn("cup", result_text)
        self.assertNotIn("tbsp", result_text)
        self.assertNotIn("large", result_text)
        self.assertNotIn("chopped", result_text)
        self.assertNotIn("clove", result_text)
    
    def test_clean_ingredient_list(self):
        """Test cleaning comma-separated ingredient strings."""
        ingredient_string = "tomatoes, onions, garlic, salt, water"
        result = self.cleaner.clean_ingredient_list(ingredient_string)
        
        # Should split and clean ingredients
        self.assertIn("tomato", result)
        self.assertIn("onion", result)
        self.assertIn("garlic", result)
        
        # Should filter out stop ingredients
        self.assertNotIn("salt", result)
        self.assertNotIn("water", result)
    
    def test_stop_ingredients_filtering(self):
        """Test that stop ingredients are properly filtered."""
        ingredients = ["water", "salt", "pepper", "tomatoes", "onions"]
        result = self.cleaner.process_ingredients(ingredients)
        
        # Should keep meaningful ingredients
        self.assertIn("tomato", result)
        self.assertIn("onion", result)
        
        # Should filter stop ingredients
        self.assertNotIn("water", result)
        self.assertNotIn("salt", result)
    
    def test_measurement_word_filtering(self):
        """Test that measurement and quantity words are properly filtered."""
        ingredients = [
            "2 cups fresh spinach",
            "1 large red bell pepper",
            "3 tbsp olive oil",
            "half cup chopped cilantro"
        ]
        result = self.cleaner.process_ingredients(ingredients)
        
        # Should keep meaningful ingredients
        self.assertIn("spinach", result)
        self.assertIn("red bell pepper", result)
        self.assertIn("cilantro", result)
        
        # Should filter measurement words
        result_text = " ".join(result)
        self.assertNotIn("cup", result_text)
        self.assertNotIn("tbsp", result_text)
        self.assertNotIn("large", result_text)
        self.assertNotIn("fresh", result_text)
        self.assertNotIn("chopped", result_text)
        self.assertNotIn("half", result_text)


if __name__ == '__main__':
    unittest.main()