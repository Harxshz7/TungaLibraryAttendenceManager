import os
import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """
    Return an absolute path to a bundled resource.

    Works for both a PyInstaller-frozen app (uses the temp _MEIPASS dir)
    and a standard source checkout (uses the project root).
    """
    base_path = getattr(sys, "_MEIPASS", None)
    if base_path:
        return os.path.join(base_path, relative_path)

    project_root = Path(__file__).resolve().parents[1]
    return str(project_root / relative_path)
