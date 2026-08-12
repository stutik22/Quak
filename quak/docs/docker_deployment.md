# 🐳 Docker Deployment Guide

This guide describes how to run and deploy the entire QWAK Recipe Recommender system using Docker and Docker Compose.

---

## 🛠️ Prerequisites
- **Docker Desktop** installed and running on your system.
- **Docker Compose** installed (typically bundled with Docker Desktop).

---

## 🏗️ Docker Compose Stack

The system is configured to orchestrate three services:
1. **`redis`**: An Alpine-based Redis container for endpoint result caching.
2. **`backend`**: FastAPI API container running on port `8000`.
3. **`frontend`**: Streamlit UI web container running on port `8501`.

---

## 🚀 Running the Application

Follow these steps to launch the entire stack:

### Step 1: Pre-train the ML models (Optional but Recommended)
The backend container mounts the local `models/` folder. For the model recommendation logic (TF-IDF & Embeddings) to work with the full dataset, you should run the training script locally first to generate the binary files:
```bash
cd training
python train_full_model.py
cd ..
```
*Note: If no models are trained, the backend container will automatically fall back to the built-in simple mock recommender.*

### Step 2: Build and Start Containers
From the root of the repository (where `docker-compose.yml` is located), run:
```bash
# Build the images
docker compose build

# Start the stack in detached (background) mode
docker compose up -d
```

### Step 3: Access the Services
Once the containers are started and healthy, you can access:
- **Streamlit Frontend (UI)**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Backend (API)**: [http://localhost:8000](http://localhost:8000)
- **FastAPI Documentation (OpenAPI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Step 4: Stop and Cleanup
To stop the services and remove the containers, run:
```bash
docker compose down
```

---

## 🐳 Useful Docker Commands

### View Service Logs
```bash
# View all logs
docker compose logs -f

# View only backend logs
docker compose logs -f backend

# View only frontend logs
docker compose logs -f frontend
```

### Check Container Status
```bash
docker compose ps
```

### Restart a Specific Service
```bash
docker compose restart backend
```
