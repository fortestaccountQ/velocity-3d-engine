import sys
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
python_dir = os.path.join(repo_root, "python")
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)
if repo_root not in sys.path:
    sys.path.insert(1, repo_root)
