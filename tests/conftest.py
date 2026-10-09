import os
import sys

# Make sure the package is importable when running tests from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
