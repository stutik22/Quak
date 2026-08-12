# QWAK Recipe Recommender - Frontend

A modern Streamlit web application for the QWAK Recipe Recommender system.

## Features

### Core Functionality
- **Ingredient Input**: Text area with smart parsing for comma-separated or line-separated ingredients
- **Recipe Recommendations**: AI-powered recipe matching using TF-IDF and Sentence-BERT models
- **Filtering**: Filter by cuisine type and dietary preferences
- **Interactive Results**: Expandable recipe cards with detailed information

### User Experience
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern UI**: Clean, gradient-based design with hover effects and animations
- **Loading States**: Progress bars and status messages during API calls
- **Error Handling**: Comprehensive error messages with troubleshooting tips

### Advanced Features
- **Search History**: Track and replay previous searches
- **Favorites System**: Save and manage favorite recipes
- **Multiple View Modes**: Cards, List, and Grid views for recipe results
- **Smart Suggestions**: Ingredient suggestions based on current input
- **Export Functionality**: Download favorite recipes as text files
- **Technical Details**: Optional display of model scores and performance metrics

### Interactive Elements
- **Quick Examples**: Pre-filled ingredient combinations for different cuisines
- **Random Ingredients**: Generate random ingredient combinations
- **Recipe Actions**: Copy ingredients, find similar recipes, share recipes
- **API Health Check**: Monitor backend service status
- **Sorting Options**: Sort results by match score, cooking time, or difficulty

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

## Configuration

### Environment Variables
- `API_BASE_URL`: Backend API URL (default: http://localhost:8000)

### Advanced Settings (in app)
- API URL configuration
- Technical details display toggle
- Auto-search on ingredient change
- Performance settings

## Usage

1. **Enter Ingredients**: Type your available ingredients in the text area
2. **Set Filters**: Choose cuisine and diet preferences in the sidebar
3. **Search**: Click "Find Recipes" to get recommendations
4. **Explore Results**: Browse recipes in your preferred view mode
5. **Save Favorites**: Click the heart icon to save recipes you like
6. **View History**: Access previous searches from the sidebar

## API Integration

The frontend communicates with the QWAK backend API:

- `POST /recommend`: Get recipe recommendations
- `GET /health`: Check API health status

### Request Format
```json
{
  "ingredients": ["tomatoes", "basil", "mozzarella"],
  "cuisine_filter": "Italian",
  "diet_filter": "vegetarian",
  "max_results": 10
}
```

### Response Format
```json
{
  "recipes": [...],
  "total_found": 25,
  "processing_time": 0.45,
  "model_info": {...}
}
```

## Responsive Design

The application adapts to different screen sizes:

- **Desktop**: Full sidebar with all features
- **Tablet**: Collapsible sidebar, optimized card layout
- **Mobile**: Stacked layout, touch-friendly buttons

## Performance Features

- **Caching**: Session state management for search history and favorites
- **Lazy Loading**: Progressive display of recipe details
- **Optimized Requests**: Efficient API communication with timeout handling
- **Memory Management**: Limited history and favorites storage

## Accessibility

- **Semantic HTML**: Proper heading structure and ARIA labels
- **Keyboard Navigation**: Full keyboard accessibility
- **Color Contrast**: High contrast colors for readability
- **Screen Reader Support**: Descriptive text and labels

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

### File Structure
```
frontend/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Key Components
- `APIClient`: Handles backend communication
- `display_recipe_card()`: Recipe card rendering
- `main()`: Main application logic and UI

### Styling
- Custom CSS for modern appearance
- Responsive design with media queries
- Gradient backgrounds and smooth transitions
- Dark mode support (system preference)