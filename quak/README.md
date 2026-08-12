# 🍳 QWAK Recipe Recommender

An AI-powered recipe recommendation system that suggests recipes based on your available ingredients using TF-IDF and Sentence-BERT models.

## 🚀 Quick Start

### Option 1: One-Click Launch (Recommended)

#### Windows
Double-click `launch.bat` or run in Command Prompt:
```cmd
launch.bat
```

#### Linux/Mac
```bash
./launch.sh
```

#### Python Launcher (Cross-platform)
```bash
python launch.py
```

### Option 2: Manual Launch

#### Start Backend
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Start Frontend (in another terminal)
```bash
cd frontend
python -m streamlit run app.py --server.port 8501
```

## 🌐 Access the Application

Once launched, access:
- **Frontend (Web App)**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Prerequisites

### Required Python Packages
```bash
pip install fastapi uvicorn streamlit requests numpy scikit-learn sentence-transformers faiss-cpu
```

### Optional Dependencies
```bash
pip install redis psutil  # For caching and monitoring
```

## 🏗️ Project Structure

```
qwak/
├── launch.py          # Cross-platform Python launcher
├── launch.bat         # Windows batch launcher
├── launch.sh          # Linux/Mac shell launcher
├── backend/           # FastAPI backend service
│   ├── main.py        # FastAPI application
│   ├── api/           # API endpoints
│   ├── core/          # Core functionality
│   ├── models/        # ML models and recommenders
│   └── utils/         # Utility functions
├── frontend/          # Streamlit web application
│   ├── app.py         # Main Streamlit app
│   └── requirements.txt
└── training/          # Model training scripts
    ├── train_tfidf.ipynb
    ├── train_embeddings.ipynb
    └── sample_recipes.csv
```

## 🤖 Features

### Backend (FastAPI)
- **Recipe Recommendation API**: Get AI-powered recipe suggestions
- **Hybrid Scoring**: Combines TF-IDF and embedding-based similarity
- **Filtering**: Support for cuisine and dietary filters
- **Caching**: Redis-based caching for performance
- **Health Monitoring**: API health checks and metrics
- **Auto-documentation**: Swagger/OpenAPI docs

### Frontend (Streamlit)
- **Modern UI**: Clean, responsive design with gradients and animations
- **Smart Input**: Ingredient parsing with suggestions
- **Interactive Results**: Expandable recipe cards with detailed info
- **Favorites System**: Save and export favorite recipes
- **Search History**: Track and replay previous searches
- **Multiple Views**: Cards, List, and Grid view modes
- **Real-time API Integration**: Live connection to backend service

## 🔧 Configuration

### Backend Configuration
Edit `backend/core/config.py` or use environment variables:

```python
# API Configuration
QWAK_DEBUG=false
QWAK_MODEL_PATH=models/

# Performance
QWAK_ENABLE_CACHING=true
QWAK_CACHE_TTL=3600
QWAK_MAX_RECOMMENDATIONS=50

# Redis (optional)
QWAK_REDIS_URL=redis://localhost:6379
QWAK_ENABLE_REDIS_CACHE=true
```

### Frontend Configuration
The frontend automatically connects to `http://localhost:8000`. To change:
- Edit `API_BASE_URL` in `frontend/app.py`
- Or use the Advanced Settings in the sidebar

## 🧪 Model Training

The system uses pre-trained models, but you can retrain them:

### TF-IDF Model
```bash
cd training
jupyter notebook train_tfidf.ipynb
```

### Embedding Model
```bash
cd training
jupyter notebook train_embeddings.ipynb
```

## 🐛 Troubleshooting

### Common Issues

#### "Connection Error" in Frontend
- Ensure backend is running on port 8000
- Check firewall settings
- Verify API URL in frontend settings

#### "Models not loaded" Error
- Check if model files exist in `backend/models/`
- Run training notebooks to generate models
- Check backend logs for loading errors

#### Port Already in Use
- Change ports in launcher scripts
- Kill existing processes: `taskkill /f /im python.exe` (Windows)

#### Import Errors
- Install missing packages: `pip install -r requirements.txt`
- Check Python version (3.8+ recommended)

### Logs and Debugging

#### View Backend Logs
```bash
# If using shell launcher
tail -f backend.log

# If running manually
# Logs appear in terminal
```

#### View Frontend Logs
```bash
# If using shell launcher
tail -f frontend.log

# If running manually
# Logs appear in terminal
```

#### Enable Debug Mode
Set `QWAK_DEBUG=true` in environment or config file.

## 🔒 Security Notes

- The application runs on localhost by default
- For production deployment, configure proper CORS settings
- Use environment variables for sensitive configuration
- Consider adding authentication for production use

## 📊 Performance

### Optimization Tips
- Enable Redis caching for better performance
- Adjust `max_results` to balance speed vs. completeness
- Use SSD storage for model files
- Increase memory allocation for large recipe databases

### Monitoring
- Backend health: http://localhost:8000/health
- Detailed metrics: http://localhost:8000/health/detailed
- Memory usage displayed in API responses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the launcher scripts
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter issues:
1. Check this README for troubleshooting steps
2. Review the logs for error messages
3. Ensure all dependencies are installed
4. Try restarting both services

## 🎯 Usage Examples

### Basic Recipe Search
1. Launch the application
2. Enter ingredients: "chicken, rice, vegetables"
3. Click "Find Recipes"
4. Browse results and save favorites

### Advanced Filtering
1. Use sidebar filters for cuisine (Italian, Asian, etc.)
2. Set dietary preferences (vegetarian, gluten-free, etc.)
3. Adjust max results slider
4. Use quick preset buttons for common combinations

### API Usage
```python
import requests

response = requests.post("http://localhost:8000/recommend", json={
    "ingredients": ["tomatoes", "basil", "mozzarella"],
    "cuisine_filter": "Italian",
    "max_results": 10
})

recipes = response.json()["recipes"]
```

---

**Happy Cooking! 🍳✨**