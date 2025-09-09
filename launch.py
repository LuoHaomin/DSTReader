"""
Simple launcher script for DST Reader.
"""

import sys
import os
from pathlib import Path

# Ensure we're in the correct directory
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Add src to Python path
src_path = script_dir / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import and run the GUI
try:
    from dstreader.gui import main as gui_main
    gui_main()
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have installed the requirements:")
    print("pip install -r requirements.txt")
    input("Press Enter to exit...")
except Exception as e:
    print(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
