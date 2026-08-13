"""
Root Streamlit Entry Point Wrapper
"""

import sys
import os

sys.path.insert(0, ".")

# Execute main dashboard app
with open("src/dashboard/app.py", "r", encoding="utf-8") as f:
    code = f.read()

exec(code)
