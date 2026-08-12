"""
QWAK Recipe Recommender - Streamlit Frontend Application
"""
import streamlit as st
import requests
import json
from typing import List, Dict, Optional
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
DEFAULT_MAX_RESULTS = 10

# Page configuration
st.set_page_config(
    page_title="QWAK Recipe Recommender",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling and responsive design
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: clamp(2rem, 5vw, 3rem);
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .recipe-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .recipe-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-color: #4ecdc4;
    }
    
    .match-score {
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    
    .ingredient-tag {
        background: #f0f2f6;
        padding: 0.2rem 0.5rem;
        border-radius: 10px;
        margin: 0.1rem;
        display: inline-block;
        font-size: 0.8rem;
        transition: background-color 0.2s;
    }
    
    .ingredient-tag:hover {
        background: #e1e5e9;
    }
    
    .error-message {
        background: #ffebee;
        color: #c62828;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #c62828;
        margin: 1rem 0;
        animation: slideIn 0.3s ease-out;
    }
    
    .success-message {
        background: #e8f5e8;
        color: #2e7d32;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2e7d32;
        margin: 1rem 0;
        animation: slideIn 0.3s ease-out;
    }
    
    .info-message {
        background: #e3f2fd;
        color: #1565c0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1565c0;
        margin: 1rem 0;
    }
    
    .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    
    .stats-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .quick-action-btn {
        margin: 0.2rem;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        border: 1px solid #ddd;
        background: white;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-block;
        font-size: 0.8rem;
    }
    
    .quick-action-btn:hover {
        background: #f0f2f6;
        border-color: #4ecdc4;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .pulsing {
        animation: pulse 1.5s infinite;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .recipe-card {
            margin: 0.5rem 0;
            padding: 0.8rem;
        }
        
        .main-header {
            padding: 1rem 0;
        }
        
        .ingredient-tag {
            font-size: 0.7rem;
            padding: 0.1rem 0.4rem;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .recipe-card {
            background: #2d3748;
            border-color: #4a5568;
            color: white;
        }
        
        .ingredient-tag {
            background: #4a5568;
            color: white;
        }
    }
</style>
""", unsafe_allow_html=True)


class APIClient:
    """Client for interacting with the QWAK Recipe Recommender API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
    
    def get_recommendations(
        self, 
        ingredients: List[str], 
        cuisine_filter: Optional[str] = None,
        diet_filter: Optional[str] = None,
        max_results: int = DEFAULT_MAX_RESULTS
    ) -> Dict:
        """Get recipe recommendations from the API."""
        try:
            # Prepare request data
            request_data = {
                "ingredients": ingredients,
                "max_results": max_results
            }
            
            if cuisine_filter and cuisine_filter != "Any":
                request_data["cuisine_filter"] = cuisine_filter
            
            if diet_filter and diet_filter != "Any":
                request_data["diet_filter"] = diet_filter
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/recommend",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                return {
                    "success": False,
                    "error": error_data.get("error", f"HTTP {response.status_code}"),
                    "detail": error_data.get("detail", "Unknown error occurred")
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Connection Error",
                "detail": "Could not connect to the recipe recommendation service. Please ensure the backend is running."
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request Timeout",
                "detail": "The request took too long to complete. Please try again."
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": "Request Error",
                "detail": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Unexpected Error",
                "detail": str(e)
            }
    
    def check_health(self) -> Dict:
        """Check API health status."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Health check failed with status {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Health check failed: {str(e)}"
            }


def display_recipe_card(recipe: Dict, index: int, show_technical: bool = False):
    """Display a recipe result card with enhanced interactivity."""
    recipe_id = recipe.get('id', index)
    
    with st.container():
        st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
        
        # Header row with match score and favorite button
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Match score badge
            match_percentage = int(recipe.get('match_score', 0) * 100)
            score_color = "#4ecdc4" if match_percentage >= 80 else "#ff6b6b" if match_percentage >= 60 else "#ffa726"
            st.markdown(
                f'<div class="match-score" style="background: {score_color};">{match_percentage}% Match</div>',
                unsafe_allow_html=True
            )
        
        with col2:
            # Favorite button
            is_favorite = recipe_id in [fav.get('id') for fav in st.session_state.favorite_recipes]
            fav_emoji = "❤️" if is_favorite else "🤍"
            
            if st.button(fav_emoji, key=f"fav_{recipe_id}", help="Add to favorites"):
                if is_favorite:
                    # Remove from favorites
                    st.session_state.favorite_recipes = [
                        fav for fav in st.session_state.favorite_recipes 
                        if fav.get('id') != recipe_id
                    ]
                    st.success("Removed from favorites!")
                else:
                    # Add to favorites
                    st.session_state.favorite_recipes.append(recipe)
                    st.success("Added to favorites!")
                st.rerun()
        
        # Recipe title with expandable details
        title = recipe.get('title', 'Unknown Recipe')
        with st.expander(f"📖 {title}", expanded=False):
            # Recipe metadata in a more organized layout
            metadata_cols = st.columns(4)
            
            with metadata_cols[0]:
                if recipe.get('cuisine'):
                    st.metric("🌍 Cuisine", recipe['cuisine'])
            
            with metadata_cols[1]:
                if recipe.get('diet'):
                    st.metric("🥗 Diet", recipe['diet'])
            
            with metadata_cols[2]:
                if recipe.get('cooking_time'):
                    st.metric("⏱️ Time", f"{recipe['cooking_time']} min")
            
            with metadata_cols[3]:
                if recipe.get('difficulty'):
                    difficulty_emoji = {
                        'Easy': '🟢',
                        'Medium': '🟡', 
                        'Hard': '🔴'
                    }.get(recipe['difficulty'], '⚪')
                    st.metric(f"{difficulty_emoji} Difficulty", recipe['difficulty'])
            
            # Full ingredients list
            if recipe.get('ingredients'):
                st.write("**All Ingredients:**")
                ingredients_html = ""
                for ingredient in recipe['ingredients']:
                    ingredients_html += f'<span class="ingredient-tag">{ingredient}</span> '
                st.markdown(ingredients_html, unsafe_allow_html=True)
                
                # Ingredient count
                st.caption(f"Total ingredients: {len(recipe['ingredients'])}")
        
        # Quick preview (always visible)
        st.write(f"**{title}**")
        
        # Quick metadata row
        quick_info = []
        if recipe.get('cuisine'):
            quick_info.append(f"🌍 {recipe['cuisine']}")
        if recipe.get('cooking_time'):
            quick_info.append(f"⏱️ {recipe['cooking_time']}min")
        if recipe.get('difficulty'):
            difficulty_emoji = {
                'Easy': '🟢',
                'Medium': '🟡', 
                'Hard': '🔴'
            }.get(recipe['difficulty'], '⚪')
            quick_info.append(f"{difficulty_emoji} {recipe['difficulty']}")
        
        if quick_info:
            st.caption(" | ".join(quick_info))
        
        # Preview ingredients (first 6)
        if recipe.get('ingredients'):
            preview_ingredients = recipe['ingredients'][:6]
            ingredients_html = ""
            for ingredient in preview_ingredients:
                ingredients_html += f'<span class="ingredient-tag">{ingredient}</span> '
            
            if len(recipe['ingredients']) > 6:
                ingredients_html += f'<span class="ingredient-tag">+{len(recipe["ingredients"]) - 6} more</span>'
            
            st.markdown(ingredients_html, unsafe_allow_html=True)
        
        # Action buttons
        action_cols = st.columns(3)
        
        with action_cols[0]:
            if st.button("📋 Copy Ingredients", key=f"copy_{recipe_id}", use_container_width=True):
                ingredients_text = "\n".join(recipe.get('ingredients', []))
                st.code(ingredients_text, language="text")
                st.success("Ingredients displayed above!")
        
        with action_cols[1]:
            if st.button("🔍 Similar Recipes", key=f"similar_{recipe_id}", use_container_width=True):
                # Store recipe for similarity search
                st.session_state.similarity_search = recipe.get('ingredients', [])
                st.info("Use these ingredients to find similar recipes!")
        
        with action_cols[2]:
            if st.button("📤 Share Recipe", key=f"share_{recipe_id}", use_container_width=True):
                share_text = f"Check out this recipe: {title}\nIngredients: {', '.join(recipe.get('ingredients', [])[:5])}..."
                st.code(share_text, language="text")
        
        # Technical details (if enabled)
        if show_technical and (recipe.get('tfidf_score') is not None or recipe.get('embedding_score') is not None):
            with st.expander("🔬 Technical Details", expanded=False):
                tech_cols = st.columns(2)
                with tech_cols[0]:
                    if recipe.get('tfidf_score') is not None:
                        st.metric("TF-IDF Score", f"{recipe['tfidf_score']:.3f}")
                with tech_cols[1]:
                    if recipe.get('embedding_score') is not None:
                        st.metric("Embedding Score", f"{recipe['embedding_score']:.3f}")
                
                # Score visualization
                if recipe.get('tfidf_score') is not None and recipe.get('embedding_score') is not None:
                    st.write("**Score Breakdown:**")
                    st.progress(recipe['tfidf_score'], text=f"TF-IDF: {recipe['tfidf_score']:.3f}")
                    st.progress(recipe['embedding_score'], text=f"Embedding: {recipe['embedding_score']:.3f}")
        
        st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main application function."""
    # Initialize session state
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'favorite_recipes' not in st.session_state:
        st.session_state.favorite_recipes = []
    if 'last_search_time' not in st.session_state:
        st.session_state.last_search_time = None
    
    # Initialize API client
    api_client = APIClient()
    
    # Header
    st.markdown('<h1 class="main-header">🍳 QWAK Recipe Recommender</h1>', unsafe_allow_html=True)
    st.markdown("**Discover delicious recipes based on your available ingredients!**")
    
    # Quick stats
    if st.session_state.search_history:
        st.markdown(
            f'<div class="stats-container">📊 You\'ve made {len(st.session_state.search_history)} searches | '
            f'❤️ {len(st.session_state.favorite_recipes)} favorites</div>',
            unsafe_allow_html=True
        )
    
    # Sidebar for filters and settings
    with st.sidebar:
        st.header("🔧 Settings & Filters")
        
        # API Health Check with auto-check on load
        api_status_container = st.container()
        
        if st.button("🔄 Check API Status"):
            with st.spinner("Checking API status..."):
                health_result = api_client.check_health()
                with api_status_container:
                    if health_result["success"]:
                        st.success("✅ API is healthy!")
                        health_data = health_result["data"]
                        st.write(f"Version: {health_data.get('version', 'Unknown')}")
                        st.write(f"Uptime: {health_data.get('uptime', 0):.1f}s")
                        
                        # Show model status
                        models = health_data.get('models_loaded', {})
                        if models:
                            st.write("**Models:**")
                            for model, status in models.items():
                                emoji = "✅" if status else "❌"
                                st.write(f"{emoji} {model}")
                    else:
                        st.error(f"❌ API Error: {health_result['error']}")
        
        st.divider()
        
        # Filters
        st.subheader("🎯 Filters")
        
        cuisine_options = ["Any", "Italian", "Asian", "Mexican", "Indian", "American", "French", "Mediterranean", "Thai", "Chinese", "Japanese", "Korean", "Greek"]
        cuisine_filter = st.selectbox("🌍 Cuisine Type", cuisine_options)
        
        diet_options = ["Any", "vegetarian", "vegan", "gluten-free", "dairy-free", "keto", "paleo", "low-carb", "high-protein"]
        diet_filter = st.selectbox("🥗 Diet Type", diet_options)
        
        max_results = st.slider("📊 Max Results", min_value=5, max_value=25, value=10)
        
        # Quick filter presets
        st.subheader("⚡ Quick Presets")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🥗 Healthy", use_container_width=True):
                st.session_state.preset_diet = "vegetarian"
                st.rerun()
        with col2:
            if st.button("🍝 Italian", use_container_width=True):
                st.session_state.preset_cuisine = "Italian"
                st.rerun()
        
        # Apply presets
        if hasattr(st.session_state, 'preset_diet'):
            diet_filter = st.session_state.preset_diet
            del st.session_state.preset_diet
        if hasattr(st.session_state, 'preset_cuisine'):
            cuisine_filter = st.session_state.preset_cuisine
            del st.session_state.preset_cuisine
        
        st.divider()
        
        # Search History
        if st.session_state.search_history:
            st.subheader("📝 Recent Searches")
            for i, search in enumerate(reversed(st.session_state.search_history[-5:])):  # Show last 5
                if st.button(f"🔍 {', '.join(search['ingredients'][:3])}{'...' if len(search['ingredients']) > 3 else ''}", 
                           key=f"history_{i}", use_container_width=True):
                    st.session_state.reload_search = search
                    st.rerun()
        
        st.divider()
        
        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            api_url = st.text_input("API URL", value=API_BASE_URL)
            if api_url != API_BASE_URL:
                api_client = APIClient(api_url)
            
            # Performance settings
            show_technical_details = st.checkbox("Show technical details", value=False)
            auto_search = st.checkbox("Auto-search on ingredient change", value=False)
            
            # Clear data
            if st.button("🗑️ Clear Search History"):
                st.session_state.search_history = []
                st.success("Search history cleared!")
            
            if st.button("💔 Clear Favorites"):
                st.session_state.favorite_recipes = []
                st.success("Favorites cleared!")
    
    # Main content area
    st.header("🥘 What ingredients do you have?")
    
    # Check for reload search from history
    if hasattr(st.session_state, 'reload_search'):
        search_data = st.session_state.reload_search
        ingredients_input = ", ".join(search_data['ingredients'])
        del st.session_state.reload_search
    else:
        ingredients_input = ""
    
    # Check for similarity search
    if hasattr(st.session_state, 'similarity_search'):
        ingredients_input = ", ".join(st.session_state.similarity_search)
        del st.session_state.similarity_search
        st.info("🔍 Searching for recipes similar to your selected recipe...")
    
    # Ingredient input with enhanced features
    input_col1, input_col2 = st.columns([3, 1])
    
    with input_col1:
        ingredients_input = st.text_area(
            "Enter your ingredients (one per line or comma-separated):",
            value=ingredients_input,
            placeholder="tomatoes\nonions\ngarlic\nbasil\nmozzarella\n\nOr try: chicken, rice, vegetables",
            height=120,
            help="💡 Tip: Be specific! Use 'chicken breast' instead of just 'chicken' for better results."
        )
    
    with input_col2:
        st.write("**Quick Actions:**")
        
        if st.button("🎲 Random Ingredients", use_container_width=True):
            import random
            random_ingredients = [
                ["chicken breast", "broccoli", "rice", "soy sauce"],
                ["pasta", "tomatoes", "basil", "mozzarella", "garlic"],
                ["salmon", "asparagus", "lemon", "olive oil", "herbs"],
                ["beef", "potatoes", "onions", "carrots", "thyme"],
                ["tofu", "vegetables", "ginger", "sesame oil", "noodles"]
            ]
            selected = random.choice(random_ingredients)
            st.session_state.random_ingredients = ", ".join(selected)
            st.rerun()
        
        if st.button("📋 Paste from Clipboard", use_container_width=True):
            st.info("Paste your ingredients in the text area!")
        
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.clear_ingredients = True
            st.rerun()
    
    # Handle random ingredients
    if hasattr(st.session_state, 'random_ingredients'):
        ingredients_input = st.session_state.random_ingredients
        del st.session_state.random_ingredients
    
    # Handle clear ingredients
    if hasattr(st.session_state, 'clear_ingredients'):
        ingredients_input = ""
        del st.session_state.clear_ingredients
    
    # Example ingredients with more variety
    st.write("**🌟 Try these ingredient combinations:**")
    example_cols = st.columns(4)
    
    examples = [
        ("🍝 Italian Classic", "tomatoes, basil, mozzarella, pasta, garlic, olive oil"),
        ("🥗 Healthy Bowl", "spinach, avocado, quinoa, chickpeas, lemon, olive oil"),
        ("🍛 Asian Fusion", "rice, soy sauce, ginger, garlic, vegetables, sesame oil"),
        ("🥩 Comfort Food", "beef, potatoes, onions, carrots, herbs, butter")
    ]
    
    for i, (name, ingredients) in enumerate(examples):
        with example_cols[i]:
            if st.button(name, use_container_width=True, key=f"example_{i}"):
                st.session_state.example_ingredients = ingredients
                st.rerun()
    
    # Use example ingredients if selected
    if hasattr(st.session_state, 'example_ingredients'):
        ingredients_input = st.session_state.example_ingredients
        del st.session_state.example_ingredients
    
    # Smart ingredient suggestions
    if ingredients_input:
        parsed_ingredients = []
        for line in ingredients_input.replace(',', '\n').split('\n'):
            ingredient = line.strip()
            if ingredient:
                parsed_ingredients.append(ingredient)
        
        if parsed_ingredients:
            st.write(f"**📝 Detected {len(parsed_ingredients)} ingredients:** {', '.join(parsed_ingredients[:5])}{'...' if len(parsed_ingredients) > 5 else ''}")
            
            # Ingredient suggestions
            suggestions = []
            if any('tomato' in ing.lower() for ing in parsed_ingredients):
                suggestions.extend(['basil', 'mozzarella', 'garlic'])
            if any('chicken' in ing.lower() for ing in parsed_ingredients):
                suggestions.extend(['thyme', 'lemon', 'onion'])
            if any('rice' in ing.lower() for ing in parsed_ingredients):
                suggestions.extend(['soy sauce', 'ginger', 'vegetables'])
            
            # Remove duplicates and ingredients already present
            suggestions = list(set(suggestions))
            suggestions = [s for s in suggestions if not any(s.lower() in ing.lower() for ing in parsed_ingredients)]
            
            if suggestions:
                st.write("**💡 Suggested additions:**")
                suggestion_html = ""
                for suggestion in suggestions[:6]:
                    suggestion_html += f'<span class="quick-action-btn" onclick="addIngredient(\'{suggestion}\')">{suggestion}</span> '
                st.markdown(suggestion_html, unsafe_allow_html=True)
    
    # Search controls
    search_cols = st.columns([2, 1, 1])
    
    with search_cols[0]:
        search_button = st.button("🔍 Find Recipes", type="primary", use_container_width=True)
    
    with search_cols[1]:
        if st.button("🎯 Smart Search", use_container_width=True, help="AI-enhanced search with suggestions"):
            st.session_state.smart_search = True
    
    with search_cols[2]:
        if st.button("⚡ Quick Search", use_container_width=True, help="Fast search with basic matching"):
            st.session_state.quick_search = True
    
    # Handle different search types
    perform_search = search_button or hasattr(st.session_state, 'smart_search') or hasattr(st.session_state, 'quick_search')
    
    if perform_search:
        # Clean up search flags
        search_type = "standard"
        if hasattr(st.session_state, 'smart_search'):
            search_type = "smart"
            del st.session_state.smart_search
        elif hasattr(st.session_state, 'quick_search'):
            search_type = "quick"
            del st.session_state.quick_search
        
        if not ingredients_input.strip():
            st.error("Please enter at least one ingredient!")
            st.stop()
        
        # Parse ingredients
        ingredients = []
        for line in ingredients_input.replace(',', '\n').split('\n'):
            ingredient = line.strip()
            if ingredient:
                ingredients.append(ingredient)
        
        if not ingredients:
            st.error("Please enter valid ingredients!")
            st.stop()
        
        # Add to search history
        search_entry = {
            'ingredients': ingredients,
            'cuisine_filter': cuisine_filter if cuisine_filter != "Any" else None,
            'diet_filter': diet_filter if diet_filter != "Any" else None,
            'timestamp': time.time(),
            'search_type': search_type
        }
        st.session_state.search_history.append(search_entry)
        st.session_state.last_search_time = time.time()
        
        # Show enhanced loading state
        loading_messages = [
            f"🔍 Analyzing {len(ingredients)} ingredients...",
            "🤖 Running AI models...",
            "📊 Calculating similarity scores...",
            "🍽️ Ranking recipes..."
        ]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, message in enumerate(loading_messages):
            status_text.text(message)
            progress_bar.progress((i + 1) / len(loading_messages))
            time.sleep(0.3)  # Simulate processing time
        
        # Get recommendations
        result = api_client.get_recommendations(
            ingredients=ingredients,
            cuisine_filter=cuisine_filter if cuisine_filter != "Any" else None,
            diet_filter=diet_filter if diet_filter != "Any" else None,
            max_results=max_results
        )
        
        # Clear loading indicators
        progress_bar.empty()
        status_text.empty()
        
        # Handle results
        if result["success"]:
            data = result["data"]
            recipes = data.get("recipes", [])
            
            if recipes:
                # Success message with enhanced info
                processing_time = data.get("processing_time", 0)
                total_found = data.get("total_found", len(recipes))
                
                st.markdown(
                    f'<div class="success-message">🎉 Found {len(recipes)} recipes (out of {total_found} total) in {processing_time:.2f} seconds!</div>',
                    unsafe_allow_html=True
                )
                
                # Search summary
                summary_cols = st.columns(4)
                with summary_cols[0]:
                    st.metric("🍽️ Recipes Found", len(recipes))
                with summary_cols[1]:
                    avg_match = sum(r.get('match_score', 0) for r in recipes) / len(recipes) * 100
                    st.metric("📊 Avg Match", f"{avg_match:.1f}%")
                with summary_cols[2]:
                    st.metric("⚡ Processing Time", f"{processing_time:.2f}s")
                with summary_cols[3]:
                    model_info = data.get("model_info", {})
                    st.metric("🤖 Models Used", len(model_info))
                
                # Display model info
                if model_info:
                    with st.expander("🔬 Model Information", expanded=False):
                        for model, info in model_info.items():
                            st.write(f"**{model}:** {info}")
                
                # Sorting and filtering options
                st.subheader("🍽️ Recipe Recommendations")
                
                sort_cols = st.columns([2, 1, 1])
                with sort_cols[0]:
                    sort_by = st.selectbox(
                        "Sort by:",
                        ["Match Score", "Cooking Time", "Difficulty", "Cuisine"],
                        key="sort_recipes"
                    )
                
                with sort_cols[1]:
                    sort_order = st.selectbox("Order:", ["Descending", "Ascending"])
                
                with sort_cols[2]:
                    view_mode = st.selectbox("View:", ["Cards", "List", "Grid"])
                
                # Sort recipes
                if sort_by == "Match Score":
                    recipes.sort(key=lambda x: x.get('match_score', 0), reverse=(sort_order == "Descending"))
                elif sort_by == "Cooking Time":
                    recipes.sort(key=lambda x: x.get('cooking_time', 999), reverse=(sort_order == "Descending"))
                elif sort_by == "Difficulty":
                    difficulty_order = {"Easy": 1, "Medium": 2, "Hard": 3}
                    recipes.sort(key=lambda x: difficulty_order.get(x.get('difficulty', 'Medium'), 2), reverse=(sort_order == "Descending"))
                
                # Display recipes based on view mode
                if view_mode == "Cards":
                    for i, recipe in enumerate(recipes):
                        display_recipe_card(recipe, i, show_technical=show_technical_details)
                        
                elif view_mode == "List":
                    for i, recipe in enumerate(recipes):
                        with st.container():
                            cols = st.columns([1, 3, 1, 1])
                            with cols[0]:
                                match_pct = int(recipe.get('match_score', 0) * 100)
                                st.metric("Match", f"{match_pct}%")
                            with cols[1]:
                                st.write(f"**{recipe.get('title', 'Unknown Recipe')}**")
                                st.caption(f"{recipe.get('cuisine', 'Unknown')} • {recipe.get('cooking_time', '?')} min")
                            with cols[2]:
                                if st.button("View", key=f"view_list_{i}"):
                                    st.session_state[f"expand_recipe_{i}"] = True
                            with cols[3]:
                                is_fav = recipe.get('id', i) in [f.get('id') for f in st.session_state.favorite_recipes]
                                if st.button("❤️" if is_fav else "🤍", key=f"fav_list_{i}"):
                                    # Handle favorite toggle
                                    pass
                            
                            if st.session_state.get(f"expand_recipe_{i}", False):
                                display_recipe_card(recipe, i, show_technical=show_technical_details)
                                if st.button("Hide", key=f"hide_{i}"):
                                    st.session_state[f"expand_recipe_{i}"] = False
                                    st.rerun()
                
                elif view_mode == "Grid":
                    # Grid view with 2 columns
                    for i in range(0, len(recipes), 2):
                        cols = st.columns(2)
                        for j, col in enumerate(cols):
                            if i + j < len(recipes):
                                with col:
                                    display_recipe_card(recipes[i + j], i + j, show_technical=show_technical_details)
                
                # Pagination for large result sets
                if len(recipes) >= max_results:
                    st.info(f"Showing top {max_results} results. Adjust the 'Max Results' slider in the sidebar to see more.")
                    
            else:
                st.warning("No recipes found matching your criteria. Try different ingredients or remove some filters.")
                
                # Suggestions for no results
                st.markdown("**💡 Suggestions:**")
                st.write("• Try more common ingredients")
                st.write("• Remove diet or cuisine filters")
                st.write("• Check spelling of ingredients")
                st.write("• Use broader ingredient terms (e.g., 'vegetables' instead of specific vegetables)")
        
        else:
            # Enhanced error handling
            st.markdown(
                f'<div class="error-message"><strong>{result["error"]}</strong><br>{result.get("detail", "")}</div>',
                unsafe_allow_html=True
            )
            
            # Error-specific suggestions
            if "connection" in result["error"].lower():
                st.markdown(
                    '<div class="info-message">💡 <strong>Troubleshooting:</strong><br>'
                    '• Make sure the backend server is running<br>'
                    '• Check the API URL in Advanced Settings<br>'
                    '• Try refreshing the page</div>',
                    unsafe_allow_html=True
                )
    
    # Favorites section
    if st.session_state.favorite_recipes:
        st.divider()
        st.header("❤️ Your Favorite Recipes")
        
        fav_cols = st.columns([3, 1])
        with fav_cols[0]:
            st.write(f"You have {len(st.session_state.favorite_recipes)} favorite recipes")
        with fav_cols[1]:
            if st.button("📤 Export Favorites"):
                favorites_text = "# My Favorite Recipes\n\n"
                for fav in st.session_state.favorite_recipes:
                    favorites_text += f"## {fav.get('title', 'Unknown Recipe')}\n"
                    favorites_text += f"**Cuisine:** {fav.get('cuisine', 'Unknown')}\n"
                    favorites_text += f"**Cooking Time:** {fav.get('cooking_time', '?')} minutes\n"
                    favorites_text += f"**Ingredients:** {', '.join(fav.get('ingredients', []))}\n\n"
                
                st.download_button(
                    "Download as Text",
                    favorites_text,
                    file_name="my_favorite_recipes.txt",
                    mime="text/plain"
                )
        
        # Display favorites in a compact format
        for i, fav_recipe in enumerate(st.session_state.favorite_recipes[-3:]):  # Show last 3
            with st.expander(f"❤️ {fav_recipe.get('title', 'Unknown Recipe')}", expanded=False):
                display_recipe_card(fav_recipe, f"fav_{i}", show_technical=False)
    
    # Footer with enhanced information
    st.divider()
    
    footer_cols = st.columns(3)
    with footer_cols[0]:
        st.markdown("**🤖 AI Models**")
        st.caption("TF-IDF + Sentence-BERT")
    
    with footer_cols[1]:
        st.markdown("**📊 Performance**")
        if st.session_state.last_search_time:
            st.caption(f"Last search: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_search_time))}")
        else:
            st.caption("No searches yet")
    
    with footer_cols[2]:
        st.markdown("**💡 Tips**")
        st.caption("Use specific ingredients for better matches")
    
    # Debug information (if enabled)
    if show_technical_details:
        with st.expander("🔧 Debug Information", expanded=False):
            st.write("**Session State:**")
            st.json({
                "search_history_count": len(st.session_state.search_history),
                "favorites_count": len(st.session_state.favorite_recipes),
                "last_search": st.session_state.last_search_time
            })


if __name__ == "__main__":
    main()