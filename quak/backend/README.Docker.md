# QWAK Backend Docker Deployment

This document describes how to deploy the QWAK Recipe Recommender backend using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB RAM available
- Model files in the `models/` directory

## Required Model Files

Before running the application, ensure the following model files are present in the `models/` directory:

- `recipe_metadata.pkl` - Recipe metadata and information
- `vectorizer.pkl` - TF-IDF vectorizer model
- `recipe_vectors_tfidf.npz` - TF-IDF recipe vectors
- `recipe_vectors_embed.npy` - Embedding recipe vectors
- `recipe_faiss_index.bin` - FAISS index for similarity search

## Quick Start

### Development Environment

1. **Clone and navigate to the backend directory:**
   ```bash
   cd qwak/backend
   ```

2. **Copy environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env file as needed
   ```

3. **Start services with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Check service status:**
   ```bash
   docker-compose ps
   ```

5. **View logs:**
   ```bash
   docker-compose logs -f backend
   ```

6. **Access the API:**
   - API: http://localhost:8000
   - Health Check: http://localhost:8000/health
   - API Documentation: http://localhost:8000/docs (if debug mode enabled)

### Production Environment

1. **Use production compose file:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Monitor services:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

## Building the Docker Image

### Build locally:
```bash
docker build -t qwak-backend:latest .
```

### Build with specific tag:
```bash
docker build -t qwak-backend:v1.0.0 .
```

### Build for production:
```bash
docker build --target production -t qwak-backend:prod .
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QWAK_DEBUG` | `false` | Enable debug mode |
| `QWAK_PRELOAD_MODELS` | `true` | Preload ML models on startup |
| `QWAK_ENABLE_CACHING` | `true` | Enable caching |
| `QWAK_ENABLE_REDIS_CACHE` | `true` | Enable Redis caching |
| `QWAK_REDIS_HOST` | `localhost` | Redis host |
| `QWAK_REDIS_PORT` | `6379` | Redis port |
| `QWAK_MAX_INGREDIENTS` | `20` | Maximum ingredients per request |
| `QWAK_REQUEST_TIMEOUT` | `30` | Request timeout in seconds |
| `QWAK_CACHE_TTL` | `3600` | Cache TTL in seconds |

## Health Checks

The application includes built-in health checks:

- **Basic Health Check:** `GET /health`
- **Detailed Health Check:** `GET /health/detailed`

Docker health checks are configured to:
- Check every 30 seconds (60s in production)
- Timeout after 10 seconds (15s in production)
- Retry 3 times before marking as unhealthy
- Wait 60 seconds before first check (120s in production)

## Troubleshooting

### Common Issues

1. **Models not loading:**
   ```bash
   # Check if model files exist
   docker-compose exec backend ls -la models/
   
   # Check logs for model loading errors
   docker-compose logs backend | grep -i model
   ```

2. **Redis connection issues:**
   ```bash
   # Check Redis status
   docker-compose exec redis redis-cli ping
   
   # Check Redis logs
   docker-compose logs redis
   ```

3. **Memory issues:**
   ```bash
   # Check container memory usage
   docker stats
   
   # Check application memory usage
   curl http://localhost:8000/health/detailed
   ```

4. **Performance issues:**
   ```bash
   # Check cache statistics
   curl http://localhost:8000/health/detailed | jq '.cache_stats'
   
   # Clear cache if needed
   curl -X POST http://localhost:8000/admin/clear-cache
   ```

### Debugging

1. **Access container shell:**
   ```bash
   docker-compose exec backend bash
   ```

2. **View application logs:**
   ```bash
   docker-compose logs -f backend
   ```

3. **Check model status:**
   ```bash
   curl http://localhost:8000/health/detailed | jq '.model_info'
   ```

4. **Reload models:**
   ```bash
   curl -X POST http://localhost:8000/admin/reload-models
   ```

## Scaling

### Horizontal Scaling

To run multiple backend instances:

```bash
docker-compose up -d --scale backend=3
```

### Load Balancer Configuration

For production, use a load balancer (nginx, HAProxy, etc.) to distribute requests:

```nginx
upstream qwak_backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://qwak_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring

### Metrics Endpoints

- `/health` - Basic health status
- `/health/detailed` - Detailed metrics including memory usage and cache stats
- `/admin/optimize-memory` - Memory optimization endpoint

### Log Monitoring

Logs are written to stdout and can be collected using:
- Docker logging drivers
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Fluentd
- Prometheus + Grafana

## Security

### Production Security Checklist

- [ ] Use non-root user (configured in Dockerfile)
- [ ] Set resource limits in docker-compose.prod.yml
- [ ] Use environment variables for sensitive configuration
- [ ] Enable Redis authentication in production
- [ ] Use HTTPS in production
- [ ] Regularly update base images
- [ ] Scan images for vulnerabilities

### Network Security

```bash
# Create custom network for isolation
docker network create qwak-network

# Run with custom network
docker-compose -f docker-compose.prod.yml --network qwak-network up -d
```

## Backup and Recovery

### Model Files Backup

```bash
# Backup model files
tar -czf models-backup-$(date +%Y%m%d).tar.gz models/

# Restore model files
tar -xzf models-backup-YYYYMMDD.tar.gz
```

### Redis Data Backup

```bash
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE
docker cp qwak-redis:/data/dump.rdb ./redis-backup-$(date +%Y%m%d).rdb
```

## Performance Tuning

### Memory Optimization

1. **Adjust model cache size:**
   ```bash
   export QWAK_MODEL_CACHE_SIZE=200  # MB
   ```

2. **Configure Redis memory:**
   ```bash
   # In docker-compose.yml
   command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
   ```

3. **Monitor memory usage:**
   ```bash
   curl http://localhost:8000/admin/optimize-memory
   ```

### Cache Optimization

1. **Adjust cache TTL:**
   ```bash
   export QWAK_CACHE_TTL=7200  # 2 hours
   ```

2. **Monitor cache hit rates:**
   ```bash
   curl http://localhost:8000/health/detailed | jq '.cache_stats'
   ```