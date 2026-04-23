"""pytest configuration – adds the project root to sys.path so that
`from app.xxx import yyy` works without needing an editable install."""
import sys
from pathlib import Path

# Insert the project root (the directory that contains the `app` package)
# at the front of sys.path so that all `app.*` imports resolve correctly.
sys.path.insert(0, str(Path(__file__).parent.parent))
