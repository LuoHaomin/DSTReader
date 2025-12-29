"""
Simple launcher script for DST Reader.
"""

import sys
import os
from pathlib import Path

def is_frozen():
    """Check if running as a PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# Handle paths for both development and PyInstaller bundle
if is_frozen():
    # Running as compiled exe
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(sys.executable).parent
    # Add the base path to sys.path (PyInstaller should already include modules)
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
else:
    # Running as script
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
    error_msg = f"Import error: {e}\nMake sure you have installed the requirements:\npip install -r requirements.txt"
    if is_frozen():
        # Show error in a message box for frozen app
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "Import Error", error_msg)
            sys.exit(1)
        except:
            # Fallback: write to file if GUI can't be shown
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(error_msg)
            sys.exit(1)
    else:
        print(error_msg)
        try:
            input("Press Enter to exit...")
        except:
            pass
        sys.exit(1)
except Exception as e:
    error_msg = f"Error starting application: {e}"
    if is_frozen():
        # Show error in a message box for frozen app
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            import traceback
            app = QApplication(sys.argv)
            tb = traceback.format_exc()
            QMessageBox.critical(None, "Application Error", f"{error_msg}\n\n{tb}")
            sys.exit(1)
        except:
            # Fallback: write to file if GUI can't be shown
            import traceback
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(error_msg + "\n\n")
                f.write(traceback.format_exc())
            sys.exit(1)
    else:
        print(error_msg)
        import traceback
        traceback.print_exc()
        try:
            input("Press Enter to exit...")
        except:
            pass
        sys.exit(1)
