import sys
import pathlib
# Add project root to PYTHONPATH for tests
project_root = pathlib.Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
