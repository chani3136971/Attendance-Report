import shutil
from pathlib import Path

print("ב-PATH:", shutil.which("tesseract"))

roots = [
    Path(r"C:\Program Files"),
    Path(r"C:\Program Files (x86)"),
    Path.home() / "AppData" / "Local" / "Programs",
    Path.home() / "AppData" / "Local",
]
for root in roots:
    if root.exists():
        for p in root.rglob("tesseract.exe"):
            print("נמצא:", p)
