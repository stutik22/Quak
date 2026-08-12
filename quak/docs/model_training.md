# 🧠 Dataset Processing & Model Training

QWAK uses precompiled models and data indices to perform fast inference. This document describes how the raw dataset is structured, cleaned, and compiled into models.

---

## 📂 Directory Layout

All data processing and training assets are located in the `training` directory:
```
training/
├── raw_recipes.csv           # Full raw recipe dataset (optional)
├── sample_recipes.csv        # Small sample dataset of 10 recipes
├── data_processor.py         # Cleaning, filtering & normalization utility
├── train_full_model.py       # Main pipeline script
├── generate_embeddings.py    # Embedding-specific training script
├── train_tfidf.ipynb         # TF-IDF training notebook
└── train_embeddings.ipynb    # Embedding training notebook
```

---

## 📊 Dataset Format

The dataset files (e.g. `raw_recipes.csv` or `sample_recipes.csv`) should be CSV files with the following headers:

| Header | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `title` | `String` | Yes | Name of the recipe (e.g., `"Margherita Pizza"`). |
| `ingredients` | `String` | Yes | Comma-separated list of raw ingredients (e.g., `"flour, tomato sauce, mozzarella, basil"`). |
| `cuisine` | `String` | No | Region/Cuisine type. If empty, the system tries to extract it using title/tag heuristics. |
| `cook_time` | `String` | No | Cooking time (e.g. `"25 minutes"` or `"1 hour 30 mins"`). |
| `difficulty` | `String` | No | Difficulty level (`Easy`, `Medium`, `Hard`). |
| `description` | `String` | No | Brief sentence about the recipe. |
| `instructions` | `String` | No | Bullet points or steps to prepare the recipe. |

---

## ⚙️ Running the Training Pipeline

The training pipeline does three things:
1. **Cleans raw data**: Lemmatizes ingredient names, removes units of measurement, and filters out non-contributing ingredients (like salt and water).
2. **Trains the TF-IDF Vectorizer**: Fits a vectorizer on the cleaned vocabulary and computes the sparse recipe matrix.
3. **Encodes Sentence Embeddings**: Uses `all-MiniLM-L6-v2` to create 384-dimensional dense vectors and builds a **FAISS** index for fast searching.

To run the pipeline and generate the model binaries:

### Using Python Command
Ensure your virtual environment is active, navigate to the `training` folder, and run `train_full_model.py`:
```bash
# Navigate to the training directory
cd training

# Run the training script
python train_full_model.py
```

*Note: If `raw_recipes.csv` is not present in the directory, the script will log a warning and automatically fall back to training on the 10-recipe `sample_recipes.csv`.*

---

## 📦 Generated Outputs

The pipeline compiles and exports files directly into the backend directory structure so that they are immediately available to the API:

| File Name | Output Directory | Purpose |
| :--- | :--- | :--- |
| `vectorizer.pkl` | `backend/models/` | Trained scikit-learn TF-IDF vectorizer object. |
| `recipe_vectors_tfidf.npz` | `backend/models/` | Compressed sparse matrix containing TF-IDF vectors for all recipes. |
| `recipe_metadata.pkl` | `backend/models/` | Serialized Python list containing metadata dicts for fast dictionary lookups. |
| `recipe_vectors_embed.npy` | `backend/models/` | NumPy binary array containing SBERT vector embeddings. |
| `recipe_faiss_index.bin` | `backend/models/` | Binary FAISS index of all recipe embeddings. |
| `embedding_metadata.pkl` | `backend/models/` | Diagnostic metadata detailing dimension, model name, and norm parameters. |
