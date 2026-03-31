import os
import sys
from pathlib import Path


def get_base_path() -> Path:
    """
    Returns the application root directory:
    - Frozen (PyInstaller): directory containing the .exe
    - Development: project root (two levels up from this file)
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[1]


def resource_path(relative_path: str) -> str:
    """
    Resolve path to a BUNDLED, read-only asset (icons, fonts, themes,
    default avatar).  In a frozen build these live inside _MEIPASS;
    in development they live in the project root.

    Use this for: assets/, themes/
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, relative_path)
    return str(get_base_path() / relative_path)


def data_path(relative_path: str) -> str:
    """
    Resolve path to USER DATA that must persist beside the executable
    and is never bundled inside _MEIPASS.

    Use this for: photos/, reports/, data/attendance.db
    """
    return str(get_base_path() / relative_path)
