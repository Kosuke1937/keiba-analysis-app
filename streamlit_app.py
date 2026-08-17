from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent / "keiba_tool_prototype_v0_3"
os.chdir(BASE_DIR)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

exec(
    (BASE_DIR / "app.py").read_text(encoding="utf-8"),
    {
        "__name__": "__main__",
        "__file__": str(BASE_DIR / "app.py"),
    },
)
