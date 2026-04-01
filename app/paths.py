# paths.py
#
# Central path definitions for the entire app.
# Every other file imports from here instead of
# computing paths themselves with __file__.

from pathlib import Path

# The root of the app — the folder containing app.py
APP_ROOT = Path(__file__).resolve().parent

# Sub-directories
MODULES_DIR = APP_ROOT / "Modules"
TABS_DIR    = APP_ROOT / "Tabs"
MARKDOWN_DIR = APP_ROOT / "Markdown"