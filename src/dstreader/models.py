"""
Data models for DST embroidery files.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import struct


@dataclass
class Stitch:
    """Represents a single stitch in the embroidery pattern."""
    
    x: int
    y: int
    jump: bool
    color_change: bool
    set_flag: int
    
    def __post_init__(self):
        """Validate stitch data after initialization."""
        # Convert numpy types to Python int if needed
        if hasattr(self.x, 'item'):
            self.x = self.x.item()
        if hasattr(self.y, 'item'):
            self.y = self.y.item()
        if hasattr(self.set_flag, 'item'):
            self.set_flag = self.set_flag.item()
            
        if not isinstance(self.x, int) or not isinstance(self.y, int):
            raise ValueError(f"Coordinates must be integers, got x={type(self.x)}, y={type(self.y)}")
        if not isinstance(self.jump, bool):
            raise ValueError("Jump flag must be boolean")
        if not isinstance(self.color_change, bool):
            raise ValueError("Color change flag must be boolean")
        if not isinstance(self.set_flag, int) or not (0 <= self.set_flag <= 3):
            raise ValueError("Set flag must be integer between 0 and 3")
    
    def __str__(self) -> str:
        """String representation of the stitch."""
        return (f"Stitch(x={self.x}, y={self.y}, jump={self.jump}, "
                f"color_change={self.color_change}, set={self.set_flag})")
    
    def __repr__(self) -> str:
        """Detailed representation of the stitch."""
        return self.__str__()
    
    @property
    def is_stitch(self) -> bool:
        """Returns True if this is a regular stitch (not a jump)."""
        return not self.jump
    
    @property
    def is_jump(self) -> bool:
        """Returns True if this is a jump stitch."""
        return self.jump
    
    @property
    def coordinates(self) -> Tuple[int, int]:
        """Returns the coordinates as a tuple."""
        return (self.x, self.y)


@dataclass
class DSTHeader:
    """Represents the header information of a DST file."""
    
    design_name: str
    stitch_count: int
    color_count: int
    pos_x: int
    neg_x: int
    pos_y: int
    neg_y: int
    ax: int
    ay: int
    mx: int
    my: int
    pd: str
    
    def __post_init__(self):
        """Validate header data after initialization."""
        if self.stitch_count < 0:
            raise ValueError("Stitch count cannot be negative")
        if self.color_count < 0:
            raise ValueError("Color count cannot be negative")
    
    @property
    def width(self) -> int:
        """Returns the total width of the design."""
        return self.pos_x + self.neg_x
    
    @property
    def height(self) -> int:
        """Returns the total height of the design."""
        return self.pos_y + self.neg_y
    
    @property
    def dimensions(self) -> Tuple[int, int]:
        """Returns the dimensions as a tuple (width, height)."""
        return (self.width, self.height)


@dataclass
class DSTFile:
    """Represents a complete DST embroidery file."""
    
    header: DSTHeader
    stitches: List[Stitch]
    file_path: Optional[str] = None
    
    def __post_init__(self):
        """Validate file data after initialization."""
        if not isinstance(self.stitches, list):
            raise ValueError("Stitches must be a list")
        if not all(isinstance(s, Stitch) for s in self.stitches):
            raise ValueError("All stitches must be Stitch objects")
    
    @property
    def stitch_count(self) -> int:
        """Returns the actual number of stitches."""
        return len(self.stitches)
    
    @property
    def jump_count(self) -> int:
        """Returns the number of jump stitches."""
        return sum(1 for stitch in self.stitches if stitch.is_jump)
    
    @property
    def regular_stitch_count(self) -> int:
        """Returns the number of regular stitches."""
        return sum(1 for stitch in self.stitches if stitch.is_stitch)
    
    @property
    def color_change_count(self) -> int:
        """Returns the number of color changes."""
        return sum(1 for stitch in self.stitches if stitch.color_change)
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Returns the bounding box as (min_x, min_y, max_x, max_y)."""
        if not self.stitches:
            return (0, 0, 0, 0)
        
        x_coords = []
        y_coords = []
        current_x = current_y = 0
        
        for stitch in self.stitches:
            current_x += stitch.x
            current_y += stitch.y
            x_coords.append(current_x)
            y_coords.append(current_y)
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    def get_path_coordinates(self) -> List[Tuple[int, int]]:
        """Returns the absolute coordinates of all stitches."""
        coordinates = []
        current_x = current_y = 0
        
        for stitch in self.stitches:
            current_x += stitch.x
            current_y += stitch.y
            coordinates.append((current_x, current_y))
        
        return coordinates
    
    def get_stitch_segments(self) -> List[List[Tuple[int, int]]]:
        """Returns segments of continuous stitches (separated by jumps)."""
        segments = []
        current_segment = []
        current_x = current_y = 0
        
        for stitch in self.stitches:
            current_x += stitch.x
            current_y += stitch.y
            
            if stitch.is_jump and current_segment:
                # End current segment and start new one
                segments.append(current_segment)
                current_segment = []
            else:
                current_segment.append((current_x, current_y))
        
        # Add the last segment if it's not empty
        if current_segment:
            segments.append(current_segment)
        
        return segments
