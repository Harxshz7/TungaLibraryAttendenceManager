import uvicorn
import os

if __name__ == "__main__":
    # Ensure working directory is the repo root for relative paths
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    uvicorn.run("web.server:app", host="0.0.0.0", port=8000)
