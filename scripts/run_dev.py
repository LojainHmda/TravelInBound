"""Dev launcher for the preview manager: disables the reloader so a single
process is tracked, then delegates to start_server.py."""
import os
import sys
import runpy

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
os.chdir(_root)
os.environ.setdefault("FLASK_USE_RELOADER", "0")
runpy.run_path(os.path.join(_root, "start_server.py"), run_name="__main__")
