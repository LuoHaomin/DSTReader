"""
Optimized DST file parser with improved performance.
"""

import os
import struct
from typing import List, Optional, Tuple, Iterator
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading

from .models import Stitch, DSTHeader, DSTFile


class OptimizedDSTParser:
    """High-performance DST file parser."""
    
    def __init__(self, use_multithreading: bool = True):
        """
        Initialize the optimized parser.
        
        Args:
            use_multithreading: Whether to use multithreading for large files
        """
        self.header_size = 512
        self.use_multithreading = use_multithreading
        self._cache = {}  # Simple file cache
        
    def parse_file(self, file_path: str, use_cache: bool = True) -> DSTFile:
        """
        Parse a DST file with optimized performance.
        
        Args:
            file_path: Path to the DST file
            use_cache: Whether to use cached results
            
        Returns:
            DSTFile object containing header and stitch data
        """
        if use_cache and file_path in self._cache:
            return self._cache[file_path]
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file size for optimization decisions
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'rb') as file:
            content = file.read()
        
        if len(content) < self.header_size:
            raise ValueError("File too small to be a valid DST file")
        
        # Parse header
        header = self._parse_header_optimized(content[:self.header_size])
        
        # Parse stitch data with optimization based on file size
        stitch_data = content[self.header_size:]
        
        if file_size > 1024 * 1024:  # Files larger than 1MB
            stitches = self._parse_stitches_optimized_large(stitch_data)
        else:
            stitches = self._parse_stitches_optimized(stitch_data)
        
        dst_file = DSTFile(header=header, stitches=stitches, file_path=file_path)
        
        # Cache the result
        if use_cache:
            self._cache[file_path] = dst_file
            
        return dst_file
    
    def _parse_header_optimized(self, header_bytes: bytes) -> DSTHeader:
        """Optimized header parsing with robust error handling."""
        try:
            # Use more efficient string operations
            header_str = header_bytes.decode('GBK', errors='ignore')
            
            # Pre-compile the parsing logic
            fields = {}
            for line in header_str.split('\r'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    fields[key] = value
            
            # Helper function to safely parse integers
            def safe_int(value, default=0):
                """Safely parse integer with fallback to default."""
                try:
                    # Remove any non-numeric characters except minus sign
                    cleaned = ''.join(c for c in value if c.isdigit() or c == '-')
                    if cleaned:
                        return int(cleaned)
                    return default
                except (ValueError, TypeError):
                    return default
            
            # Create header with safe parsing
            return DSTHeader(
                design_name=fields.get('LA', ''),
                stitch_count=safe_int(fields.get('ST', '0')),
                color_count=safe_int(fields.get('CO', '0')),
                pos_x=safe_int(fields.get('+X', '0')),
                neg_x=safe_int(fields.get('-X', '0')),
                pos_y=safe_int(fields.get('+Y', '0')),
                neg_y=safe_int(fields.get('-Y', '0')),
                ax=safe_int(fields.get('AX', '0')),
                ay=safe_int(fields.get('AY', '0')),
                mx=safe_int(fields.get('MX', '0')),
                my=safe_int(fields.get('MY', '0')),
                pd=fields.get('PD', '')
            )
            
        except Exception as e:
            # If header parsing fails completely, create a minimal header
            print(f"Warning: Header parsing failed ({e}), using default values")
            return DSTHeader(
                design_name="Unknown",
                stitch_count=0,
                color_count=0,
                pos_x=0, neg_x=0, pos_y=0, neg_y=0,
                ax=0, ay=0, mx=0, my=0, pd=""
            )
    
    def _parse_stitches_optimized(self, stitch_data: bytes) -> List[Stitch]:
        """Optimized stitch parsing for smaller files."""
        stitch_count = len(stitch_data) // 3
        stitches = []
        
        # Pre-allocate list for better performance
        stitches = [None] * stitch_count
        
        # Use numpy for faster bit operations
        data_array = np.frombuffer(stitch_data, dtype=np.uint8)
        data_array = data_array.reshape(-1, 3)
        
        for i, (byte0, byte1, byte2) in enumerate(data_array):
            # Optimized coordinate calculation using bitwise operations
            x = self._calculate_x_coordinate(byte0, byte1, byte2)
            y = self._calculate_y_coordinate(byte0, byte1, byte2)
            
            # Parse flags
            jump = bool(byte2 & 0b10000000)
            color_change = bool(byte2 & 0b01000000)
            set_flag = byte2 & 0b00000011
            
            stitches[i] = Stitch(x=x, y=y, jump=jump, color_change=color_change, set_flag=set_flag)
        
        return stitches
    
    def _parse_stitches_optimized_large(self, stitch_data: bytes) -> List[Stitch]:
        """Optimized stitch parsing for large files using multithreading."""
        stitch_count = len(stitch_data) // 3
        
        if not self.use_multithreading or stitch_count < 10000:
            return self._parse_stitches_optimized(stitch_data)
        
        # Split data into chunks for parallel processing
        chunk_size = max(1000, stitch_count // 4)  # Process in 4 threads
        chunks = []
        
        for i in range(0, stitch_count, chunk_size):
            end_idx = min(i + chunk_size, stitch_count)
            start_byte = i * 3
            end_byte = end_idx * 3
            chunks.append((i, stitch_data[start_byte:end_byte]))
        
        # Pre-allocate result list
        stitches = [None] * stitch_count
        
        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for start_idx, chunk_data in chunks:
                future = executor.submit(self._parse_stitch_chunk, chunk_data, start_idx)
                futures.append(future)
            
            # Collect results
            for future in futures:
                chunk_stitches, start_idx = future.result()
                for i, stitch in enumerate(chunk_stitches):
                    stitches[start_idx + i] = stitch
        
        return stitches
    
    def _parse_stitch_chunk(self, chunk_data: bytes, start_idx: int) -> Tuple[List[Stitch], int]:
        """Parse a chunk of stitch data."""
        chunk_stitches = []
        
        for i in range(0, len(chunk_data), 3):
            if i + 3 > len(chunk_data):
                break
                
            byte0, byte1, byte2 = chunk_data[i:i+3]
            
            x = self._calculate_x_coordinate(byte0, byte1, byte2)
            y = self._calculate_y_coordinate(byte0, byte1, byte2)
            
            jump = bool(byte2 & 0b10000000)
            color_change = bool(byte2 & 0b01000000)
            set_flag = byte2 & 0b00000011
            
            chunk_stitches.append(Stitch(x=x, y=y, jump=jump, color_change=color_change, set_flag=set_flag))
        
        return chunk_stitches, start_idx
    
    def _calculate_x_coordinate(self, byte0: int, byte1: int, byte2: int) -> int:
        """Calculate X coordinate using optimized bit operations."""
        x = 0
        x += ((byte0 & 0b00000001) * 1) + ((byte0 & 0b00000010) >> 1) * (-1)
        x += ((byte0 & 0b00000100) >> 2) * 9 + ((byte0 & 0b00001000) >> 3) * (-9)
        x += ((byte1 & 0b00000001) * 3) + ((byte1 & 0b00000010) >> 1) * (-3)
        x += ((byte1 & 0b00000100) >> 2) * 27 + ((byte1 & 0b00001000) >> 3) * (-27)
        x += ((byte2 & 0b00000100) >> 2) * 81 + ((byte2 & 0b00001000) >> 3) * (-81)
        return x
    
    def _calculate_y_coordinate(self, byte0: int, byte1: int, byte2: int) -> int:
        """Calculate Y coordinate using optimized bit operations."""
        y = 0
        y += ((byte0 & 0b10000000) >> 7) * 1 + ((byte0 & 0b01000000) >> 6) * (-1)
        y += ((byte0 & 0b00100000) >> 5) * 9 + ((byte0 & 0b00010000) >> 4) * (-9)
        y += ((byte1 & 0b10000000) >> 7) * 3 + ((byte1 & 0b01000000) >> 6) * (-3)
        y += ((byte1 & 0b00100000) >> 5) * 27 + ((byte1 & 0b00010000) >> 4) * (-27)
        y += ((byte2 & 0b00001000) >> 3) * 81 + ((byte2 & 0b00000100) >> 2) * (-81)
        return y
    
    def get_header_info_fast(self, file_path: str) -> dict:
        """
        Get header information without parsing all stitches (very fast).
        
        Args:
            file_path: Path to the DST file
            
        Returns:
            Dictionary with header information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'rb') as file:
            header_bytes = file.read(self.header_size)
        
        if len(header_bytes) < self.header_size:
            raise ValueError("File too small to be a valid DST file")
        
        header = self._parse_header_optimized(header_bytes)
        file_size = os.path.getsize(file_path)
        
        return {
            'design_name': header.design_name,
            'stitch_count': header.stitch_count,
            'color_count': header.color_count,
            'dimensions': header.dimensions,
            'file_size': file_size,
            'file_path': file_path
        }
    
    def validate_file_fast(self, file_path: str) -> bool:
        """
        Fast validation of DST file format.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if valid DST file, False otherwise
        """
        try:
            self.get_header_info_fast(file_path)
            return True
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear the file cache."""
        self._cache.clear()
    
    def get_cache_info(self) -> dict:
        """Get information about the cache."""
        return {
            'cached_files': len(self._cache),
            'cache_keys': list(self._cache.keys())
        }


# Backward compatibility
DSTParser = OptimizedDSTParser