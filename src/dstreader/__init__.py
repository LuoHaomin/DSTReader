"""
DST Reader - A Python library for reading and visualizing DST embroidery files.

This package provides functionality to:
- Parse DST embroidery files
- Extract stitch data and metadata
- Visualize embroidery patterns with PyQt GUI
- Generate static images and animations
"""

__version__ = "1.0.0"
__author__ = "DST Reader Team"

from .models import Stitch, DSTFile, DSTHeader
from .parser import DSTParser, OptimizedDSTParser
from .visualizer import DSTVisualizer

# GUI components
try:
    from .gui import DSTMainWindow, DSTCanvas
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

__all__ = [
    "Stitch",
    "DSTFile", 
    "DSTHeader",
    "DSTParser",
    "OptimizedDSTParser",
    "DSTVisualizer",
]

if GUI_AVAILABLE:
    __all__.extend([
        "DSTMainWindow",
        "DSTCanvas"
    ])
