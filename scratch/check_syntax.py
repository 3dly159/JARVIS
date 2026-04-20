import sys
import os
sys.path.append(os.getcwd())

import logging
logging.basicConfig(level=logging.INFO)

try:
    from core.cognition import CognitionLoop
    loop = CognitionLoop()
    print("SUCCESS: CognitionLoop initialized without syntax errors.")
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
