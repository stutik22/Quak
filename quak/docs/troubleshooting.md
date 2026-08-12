# 🐛 Troubleshooting Guide

This guide details common issues you may encounter when setting up or running the QWAK Recipe Recommender, along with their solutions.

---

## 🚫 Common Startup & Launch Errors

### 1. `UnicodeEncodeError` when running `launch.py`
* **Symptoms**:
  ```
  UnicodeEncodeError: 'charmap' codec can't encode characters: character maps to <undefined>
  ```
* **Cause**: On Windows systems, the CMD/PowerShell terminal output stream defaults to `CP1252` encoding, which cannot render the emoji or box-drawing characters used in the application banner.
* **Solution**: The launcher has been updated to force the standard output/error stream to use `UTF-8` encoding. Always execute using Python:
  ```bash
  python launch.py
  ```
  Or if you run without virtual environment activation, run:
  ```bash
  .venv\Scripts\python.exe launch.py
  ```

### 2. `ModuleNotFoundError: No module named 'nltk'` (or other package)
* **Symptoms**:
  ```
  ModuleNotFoundError: No module named 'nltk'
  ```
* **Cause**: Running Python globally instead of within the virtual environment where dependencies are installed, or a package was missing from the `requirements.txt`.
* **Solution**: Ensure your virtual environment is active before running scripts, or run them explicitly via the `.venv` executable. We have added `nltk>=3.8.1` to [backend/requirements.txt](file:///c:/Users/Stuti/OneDrive/Desktop/quak/quak/backend/requirements.txt).
  ```bash
  # Re-install dependencies
  .venv\Scripts\pip.exe install -r backend/requirements.txt -r frontend/requirements.txt
  ```

### 3. `faiss-cpu` Installation Failure
* **Symptoms**:
  ```
  ERROR: Could not find a version that satisfies the requirement faiss-cpu==1.7.4
  ERROR: No matching distribution found for faiss-cpu==1.7.4
  ```
* **Cause**: Strict package version pins (`==1.7.4`) do not have pre-built wheels for newer Python versions (like Python 3.12) on Windows, forcing a compilation from source which fails if C++ build tools are missing.
* **Solution**: Version constraints for ML packages have been loosened in the requirements file to use `>=` boundaries. This allows pip to fetch newer pre-compiled wheels (e.g. `faiss-cpu 1.8.0` or higher) that support Python 3.12 out-of-the-box.

---

## 🍽️ Recommendation & Search Issues

### 1. "No recipes found matching your criteria"
* **Symptoms**: You type valid ingredients but the UI shows a warning banner and returns `0` recipes.
* **Cause**:
  * **Incorrect API Route**: The frontend client was historically querying `/api/v1/recommend`, which returned a `404 Not Found` error.
  * **Model Files Missing**: The models were not trained yet.
  * **Filter mismatch**: You have left a restrictive cuisine or diet filter active in the sidebar that none of the matching recipes satisfy.
* **Solution**:
  * Ensure the API route in [app.py](file:///c:/Users/Stuti/OneDrive/Desktop/quak/quak/frontend/app.py) is set to `/recommend` (this has been fixed).
  * Go to the `training` folder and run `python train_full_model.py` to generate the vector assets.
  * Clear filters in the sidebar (set them to **"Any"**) and search again.

### 2. `Redis connection failed: Error 10061 connecting to localhost:6379`
* **Symptoms**: Backend prints:
  ```
  [Backend] Redis connection failed: Error 10061 connecting to localhost:6379... Falling back to memory cache.
  ```
* **Cause**: Redis server is not running on your machine, or is running on a different port.
* **Solution**: This is a **warning** and does not crash the system. The backend automatically switches to a fast in-memory dictionary cache. If you want to use Redis, start the Redis service on your PC or configure `QWAK_REDIS_URL` in your `.env` file.

### 3. Port Already in Use (Port `8000` or `8501`)
* **Symptoms**: Backend or Frontend fails to bind to port and exits immediately.
* **Solution**: Kill any lingering Python processes running in the background.
  * **Windows (CMD/PowerShell)**:
    ```powershell
    # Find python processes
    Get-Process -Name python*
    
    # Kill python processes
    kill -Name python
    ```
  * Or edit the ports in `launch.py` (lines 16-17) to use different numbers.
