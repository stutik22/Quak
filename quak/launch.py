#!/usr/bin/env python3
"""
QWAK Recipe Recommender - Application Launcher
Starts both backend API and frontend Streamlit app simultaneously.
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

# Reconfigure stdout/stderr to UTF-8 to support unicode characters on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


# Configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 8501
BACKEND_DIR = "backend"
FRONTEND_DIR = "frontend"

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message, color=Colors.OKBLUE):
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.ENDC}")

def print_banner():
    """Print application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🍳 QWAK Recipe Recommender                ║
    ║                     Application Launcher                     ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print_colored(banner, Colors.HEADER)

def check_dependencies():
    """Check if required dependencies are installed."""
    print_colored("🔍 Checking dependencies...", Colors.OKCYAN)
    
    # Check Python packages
    required_packages = {
        'fastapi': 'FastAPI backend framework',
        'uvicorn': 'ASGI server for FastAPI',
        'streamlit': 'Frontend web framework',
        'requests': 'HTTP client for frontend'
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            print_colored(f"  ✅ {package} - {description}", Colors.OKGREEN)
        except ImportError:
            print_colored(f"  ❌ {package} - {description}", Colors.FAIL)
            missing_packages.append(package)
    
    if missing_packages:
        print_colored(f"\n❌ Missing packages: {', '.join(missing_packages)}", Colors.FAIL)
        print_colored("Please install missing packages:", Colors.WARNING)
        print_colored(f"  pip install {' '.join(missing_packages)}", Colors.OKBLUE)
        return False
    
    print_colored("✅ All dependencies are installed!", Colors.OKGREEN)
    return True

def check_models():
    """Check if required model files exist."""
    print_colored("🤖 Checking model files...", Colors.OKCYAN)
    
    model_dir = Path(BACKEND_DIR) / "models"
    required_files = [
        "vectorizer.pkl",
        "recipe_vectors_tfidf.npz",
        "recipe_metadata.pkl",
        "recipe_vectors_embed.npy",
        "embedding_metadata.pkl"
    ]
    
    missing_files = []
    
    for file_name in required_files:
        file_path = model_dir / file_name
        if file_path.exists():
            print_colored(f"  ✅ {file_name}", Colors.OKGREEN)
        else:
            print_colored(f"  ❌ {file_name}", Colors.FAIL)
            missing_files.append(file_name)
    
    if missing_files:
        print_colored(f"\n⚠️  Missing model files: {', '.join(missing_files)}", Colors.WARNING)
        print_colored("Some features may not work properly.", Colors.WARNING)
        print_colored("Run the training scripts to generate missing models.", Colors.OKBLUE)
    else:
        print_colored("✅ All model files are present!", Colors.OKGREEN)
    
    return len(missing_files) == 0

def start_backend():
    """Start the FastAPI backend server."""
    print_colored("🚀 Starting backend server...", Colors.OKCYAN)
    
    backend_path = Path(BACKEND_DIR)
    if not backend_path.exists():
        print_colored(f"❌ Backend directory not found: {backend_path}", Colors.FAIL)
        return None
    
    try:
        # Change to backend directory and start uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", str(BACKEND_PORT),
            "--reload"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd=backend_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print_colored(f"✅ Backend server starting on http://localhost:{BACKEND_PORT}", Colors.OKGREEN)
        return process
        
    except Exception as e:
        print_colored(f"❌ Failed to start backend: {e}", Colors.FAIL)
        return None

def start_frontend():
    """Start the Streamlit frontend app."""
    print_colored("🎨 Starting frontend app...", Colors.OKCYAN)
    
    frontend_path = Path(FRONTEND_DIR)
    if not frontend_path.exists():
        print_colored(f"❌ Frontend directory not found: {frontend_path}", Colors.FAIL)
        return None
    
    try:
        # Change to frontend directory and start streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "app.py",
            "--server.port", str(FRONTEND_PORT),
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd=frontend_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print_colored(f"✅ Frontend app starting on http://localhost:{FRONTEND_PORT}", Colors.OKGREEN)
        return process
        
    except Exception as e:
        print_colored(f"❌ Failed to start frontend: {e}", Colors.FAIL)
        return None

def monitor_process(process, name, color=Colors.OKBLUE):
    """Monitor a process and print its output."""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                # Filter out some verbose logs
                if any(skip in line.lower() for skip in ['info:', 'debug:', 'warning:']):
                    continue
                print_colored(f"[{name}] {line.strip()}", color)
    except Exception as e:
        print_colored(f"[{name}] Monitor error: {e}", Colors.FAIL)

def wait_for_services():
    """Wait for services to be ready."""
    print_colored("⏳ Waiting for services to start...", Colors.OKCYAN)
    
    import requests
    import time
    
    # Wait for backend
    backend_ready = False
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"http://localhost:{BACKEND_PORT}/health", timeout=2)
            if response.status_code == 200:
                backend_ready = True
                print_colored("✅ Backend is ready!", Colors.OKGREEN)
                break
        except:
            pass
        time.sleep(1)
    
    if not backend_ready:
        print_colored("⚠️  Backend may not be ready yet", Colors.WARNING)
    
    # Give frontend a moment to start
    time.sleep(3)
    print_colored("✅ Frontend should be ready!", Colors.OKGREEN)

def main():
    """Main launcher function."""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check models (warning only)
    check_models()
    
    print_colored("\n🚀 Starting QWAK Recipe Recommender...", Colors.HEADER)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print_colored("❌ Failed to start backend. Exiting.", Colors.FAIL)
        sys.exit(1)
    
    # Wait a moment for backend to initialize
    time.sleep(2)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print_colored("❌ Failed to start frontend. Stopping backend.", Colors.FAIL)
        backend_process.terminate()
        sys.exit(1)
    
    # Start monitoring threads
    backend_thread = threading.Thread(
        target=monitor_process, 
        args=(backend_process, "Backend", Colors.OKBLUE),
        daemon=True
    )
    frontend_thread = threading.Thread(
        target=monitor_process, 
        args=(frontend_process, "Frontend", Colors.OKCYAN),
        daemon=True
    )
    
    backend_thread.start()
    frontend_thread.start()
    
    # Wait for services to be ready
    wait_for_services()
    
    # Print success message
    print_colored("\n" + "="*60, Colors.OKGREEN)
    print_colored("🎉 QWAK Recipe Recommender is now running!", Colors.OKGREEN)
    print_colored("="*60, Colors.OKGREEN)
    print_colored(f"🔗 Frontend: http://localhost:{FRONTEND_PORT}", Colors.HEADER)
    print_colored(f"🔗 Backend API: http://localhost:{BACKEND_PORT}", Colors.HEADER)
    print_colored(f"📚 API Docs: http://localhost:{BACKEND_PORT}/docs", Colors.HEADER)
    print_colored("="*60, Colors.OKGREEN)
    print_colored("\n💡 Press Ctrl+C to stop both services", Colors.WARNING)
    
    try:
        # Keep the main process alive
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print_colored("❌ Backend process stopped unexpectedly", Colors.FAIL)
                break
            if frontend_process.poll() is not None:
                print_colored("❌ Frontend process stopped unexpectedly", Colors.FAIL)
                break
            time.sleep(1)
    
    except KeyboardInterrupt:
        print_colored("\n🛑 Shutting down services...", Colors.WARNING)
    
    finally:
        # Clean shutdown
        print_colored("🧹 Cleaning up processes...", Colors.OKCYAN)
        
        try:
            backend_process.terminate()
            frontend_process.terminate()
            
            # Wait for graceful shutdown
            backend_process.wait(timeout=5)
            frontend_process.wait(timeout=5)
            
        except subprocess.TimeoutExpired:
            print_colored("⚠️  Force killing processes...", Colors.WARNING)
            backend_process.kill()
            frontend_process.kill()
        
        except Exception as e:
            print_colored(f"⚠️  Cleanup error: {e}", Colors.WARNING)
        
        print_colored("✅ Shutdown complete!", Colors.OKGREEN)

if __name__ == "__main__":
    main()