#!/bin/bash

# QWAK Backend Startup Script

set -e

echo "Starting QWAK Recipe Recommender Backend..."

# Check if models directory exists and has required files
if [ ! -d "models" ]; then
    echo "Warning: Models directory not found. Creating empty directory."
    mkdir -p models
fi

# Check for required model files
REQUIRED_FILES=(
    "models/recipe_metadata.pkl"
    "models/vectorizer.pkl"
    "models/recipe_vectors_tfidf.npz"
    "models/recipe_vectors_embed.npy"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo "Warning: Missing model files:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    echo "The application may not function properly without these files."
fi

# Wait for Redis if enabled
if [ "$QWAK_ENABLE_REDIS_CACHE" = "true" ]; then
    echo "Waiting for Redis to be ready..."
    
    REDIS_HOST=${QWAK_REDIS_HOST:-localhost}
    REDIS_PORT=${QWAK_REDIS_PORT:-6379}
    
    # Wait up to 30 seconds for Redis
    for i in {1..30}; do
        if python -c "import redis; redis.Redis(host='$REDIS_HOST', port=$REDIS_PORT, socket_timeout=1).ping()" 2>/dev/null; then
            echo "Redis is ready!"
            break
        fi
        
        if [ $i -eq 30 ]; then
            echo "Warning: Redis not available after 30 seconds. Continuing without Redis cache."
            export QWAK_ENABLE_REDIS_CACHE=false
        else
            echo "Waiting for Redis... ($i/30)"
            sleep 1
        fi
    done
fi

# Set default values for environment variables
export QWAK_DEBUG=${QWAK_DEBUG:-false}
export QWAK_PRELOAD_MODELS=${QWAK_PRELOAD_MODELS:-true}
export QWAK_ENABLE_CACHING=${QWAK_ENABLE_CACHING:-true}

echo "Environment configuration:"
echo "  DEBUG: $QWAK_DEBUG"
echo "  PRELOAD_MODELS: $QWAK_PRELOAD_MODELS"
echo "  ENABLE_CACHING: $QWAK_ENABLE_CACHING"
echo "  ENABLE_REDIS_CACHE: $QWAK_ENABLE_REDIS_CACHE"

# Start the application
echo "Starting FastAPI application..."
exec python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --log-level ${QWAK_LOG_LEVEL:-info} \
    --access-log