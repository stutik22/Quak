# 📚 API Reference Documentation

The QWAK Recipe Recommender backend is built using FastAPI and exposes endpoints for recipe recommendations, health checking, and system administration.

By default, the backend runs on: **`http://localhost:8000`**

---

## 🍽️ Recommendation Endpoints

### 1. Get Recommendations
Retrieves recipe recommendations matching the given ingredients, filtered by cuisine or diet types.

* **Endpoint**: `POST /recommend`
* **Content-Type**: `application/json`

#### Request Body
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `ingredients` | `List[str]` | Yes | A list of 1 to 20 ingredient strings. Names must be $< 100$ characters. |
| `cuisine_filter` | `String` | No | Filter recipes by cuisine (e.g., `"Italian"`, `"Indian"`). |
| `diet_filter` | `String` | No | Filter recipes by diet restrictions (e.g., `"vegetarian"`, `"vegan"`). |
| `max_results` | `Integer` | No | Maximum recommendations to return (default: `10`, range: `1-50`). |

#### Example Request
```json
{
  "ingredients": ["pasta", "eggs", "bacon"],
  "cuisine_filter": "Italian",
  "max_results": 2
}
```

#### Example Response
```json
{
  "recipes": [
    {
      "id": 1,
      "title": "Spaghetti Carbonara",
      "ingredients": ["spaghetti", "egg", "bacon", "parmesan cheese", "black pepper", "garlic"],
      "cuisine": "Italian",
      "diet": "Regular",
      "cooking_time": 20,
      "difficulty": "Medium",
      "match_score": 0.9452,
      "tfidf_score": 0.892,
      "embedding_score": 0.981
    }
  ],
  "total_found": 1,
  "processing_time": 0.042,
  "model_info": {
    "tfidf_available": true,
    "embedding_available": true,
    "hybrid_scorer_available": true,
    "tfidf_weight": 0.4,
    "embedding_weight": 0.6
  }
}
```

### 2. Get Filter Options
Retrieves all unique cuisines and diet restrictions present in the loaded dataset to populate UI select boxes.

* **Endpoint**: `GET /recommend/filters`

#### Example Response
```json
{
  "cuisines": ["Italian", "Indian", "Chinese", "Thai", "French", "American", "Mediterranean", "Other"],
  "diets": ["Regular", "Vegetarian", "Vegan", "Gluten-Free", "Low-Carb", "Keto"]
}
```

---

## 🏥 Health & Monitoring Endpoints

### 1. Basic Health Check
Returns the availability status of the API and which ML models are preloaded in memory.

* **Endpoint**: `GET /health`

#### Example Response
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "models_loaded": {
    "simple_loaded": true,
    "tfidf_loaded": true,
    "embedding_loaded": true,
    "hybrid_loaded": true,
    "manager_loaded": true
  },
  "uptime": 124.5
}
```

### 2. Detailed Health Check
Returns detailed system diagnostics, memory footprint, cache statistics, and runtime configurations.

* **Endpoint**: `GET /health/detailed`

#### Example Response
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 124.5,
  "model_info": {
    "status": {
      "simple_loaded": true,
      "tfidf_loaded": true,
      "embedding_loaded": true,
      "hybrid_loaded": true,
      "manager_loaded": true
    },
    "load_times": {},
    "memory_usage": {
      "rss_mb": 254.3,
      "vms_mb": 1184.2,
      "percent": 1.5,
      "available_mb": 8432.1
    },
    "cache_stats": {
      "hits": 14,
      "misses": 3,
      "size": 3
    },
    "models_available": [],
    "hybrid_available": true
  },
  "settings": {
    "preload_models": true,
    "enable_caching": true,
    "enable_redis_cache": true,
    "max_ingredients": 20,
    "request_timeout": 30
  }
}
```

---

## 🛠️ Administrative Endpoints (POST)

These administrative endpoints are available for hot-reloading configurations and cache maintenance:

| Endpoint | Description |
| :--- | :--- |
| `POST /admin/reload-models` | Unloads and re-reads all ML vectorizers, FAISS binaries, and metadata files from the `backend/models` folder. |
| `POST /admin/clear-cache` | Flushes all query cache entries from memory and/or Redis. |
| `POST /admin/optimize-memory` | Triggers manual garbage collection (`gc.collect()`) and clears temporary variables to free RAM. |
