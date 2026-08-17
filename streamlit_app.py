from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent / "keiba_tool_prototype_v0_3"
os.chdir(BASE_DIR)

exec(
    (BASE_DIR / "app.py").read_text(encoding="utf-8"),
    {
        "__name__": "__main__",
        "__file__": str(BASE_DIR / "app.py"),
    },
)
