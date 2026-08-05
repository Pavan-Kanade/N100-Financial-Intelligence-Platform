import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if "." not in sys.path:
    sys.path.insert(0, ".")

with open("src/dashboard/pages/04_peers.py", "r", encoding="utf-8") as f:
    code = f.read()

exec(code)
