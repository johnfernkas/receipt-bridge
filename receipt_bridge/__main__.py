import sys
from pathlib import Path
from .daemon import run

if __name__ == "__main__":
    config = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    run(*([config] if config else []))
