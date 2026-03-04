import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for path in [
    ROOT / "services" / "api",
    ROOT / "services" / "worker",
    ROOT / "services" / "remediator",
]:
    sys.path.insert(0, str(path))
