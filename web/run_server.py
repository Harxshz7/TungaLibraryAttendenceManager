import uvicorn
import os
import sys

if __name__ == "__main__":
    # Ensure working directory and sys.path include the repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_root)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
        
    uvicorn.run("web.server:app", host="0.0.0.0", port=8000)
