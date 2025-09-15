"""
Visualization module for DST embroidery files.
"""

import os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from typing import List, Optional, Tuple
import numpy as np

from .models import DSTFile, Stitch


class DSTVisualizer:
    """Visualizer for DST embroidery files."""
    
    def __init__(self, backend: str = 'Agg', font_family: str = 'Microsoft YaHei'):
        """
        Initialize the visualizer.
        
        Args:
            backend: Matplotlib backend to use
            font_family: Font family for Chinese text
        """
        matplotlib.use(backend)
        matplotlib.rc("font", family=font_family)
        self.backend = backend
        self.font_family = font_family
    
    def set_backend(self, backend: str, interactive: bool = False):
        """
        Set matplotlib backend.
        
        Args:
            backend: Backend name ('Agg' for non-interactive, 'TkAgg' for interactive)
            interactive: Whether to use interactive backend
        """
        if interactive:
            matplotlib.use('TkAgg')
        else:
            matplotlib.use(backend)
        self.backend = matplotlib.get_backend()
    
    def create_static_plot(self, dst_file: DSTFile, 
                          output_path: Optional[str] = None,
                          title: Optional[str] = None,
                          figsize: Tuple[int, int] = (10, 8),
                          dpi: int = 300) -> str:
        """
        Create a static plot of the embroidery pattern.
        
        Args:
            dst_file: DSTFile object to visualize
            output_path: Output file path (optional)
            title: Plot title (optional)
            figsize: Figure size tuple
            dpi: DPI for output image
            
        Returns:
            Path to the saved image file
        """
        plt.clf()
        
        # Get path coordinates
        coordinates = dst_file.get_path_coordinates()
        if not coordinates:
            raise ValueError("No coordinates found in DST file")
        
        # Separate coordinates
        x_coords = [coord[0] for coord in coordinates]
        y_coords = [coord[1] for coord in coordinates]
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Determine colors for each segment
        stitch_segments = dst_file.get_stitch_segments()
        
        for segment in stitch_segments:
            if len(segment) > 1:
                seg_x = [coord[0] for coord in segment]
                seg_y = [coord[1] for coord in segment]
                ax.plot(seg_x, seg_y, 'b-', linewidth=2, alpha=0.8)
        
        # Plot individual points
        ax.plot(x_coords, y_coords, 'ko', markersize=2, alpha=0.6)
        
        # Set title
        if title is None:
            title = dst_file.header.design_name or "DST Embroidery Pattern"
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Set labels and grid
        ax.set_xlabel("X Coordinate", fontsize=12)
        ax.set_ylabel("Y Coordinate", fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Set equal aspect ratio and invert Y axis
        ax.set_aspect('equal')
        # ax.invert_yaxis()
        
        # Determine output path
        if output_path is None:
            base_name = dst_file.file_path or "dst_pattern"
            output_path = f"{os.path.splitext(base_name)[0]}_static.png"
        
        # Save the plot
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def create_animation(self, dst_file: DSTFile,
                        output_path: Optional[str] = None,
                        frame_duration: int = 200,
                        show_window: bool = False,
                        figsize: Tuple[int, int] = (12, 10)) -> str:
        """
        Create an animated GIF of the embroidery pattern being drawn.
        
        Args:
            dst_file: DSTFile object to animate
            output_path: Output file path (optional)
            frame_duration: Duration of each frame in milliseconds
            show_window: Whether to show the animation window
            figsize: Figure size tuple
            
        Returns:
            Path to the saved GIF file
        """
        coordinates = dst_file.get_path_coordinates()
        if not coordinates:
            raise ValueError("No coordinates found in DST file")
        
        # Set interactive backend if showing window
        if show_window:
            self.set_backend('TkAgg', interactive=True)
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Calculate bounds
        x_coords = [coord[0] for coord in coordinates]
        y_coords = [coord[1] for coord in coordinates]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Add margin
        margin = max(x_max - x_min, y_max - y_min) * 0.1
        ax.set_xlim(x_min - margin, x_max + margin)
        ax.set_ylim(y_min - margin, y_max + margin)
        
        # Set aspect ratio and invert Y axis
        ax.set_aspect('equal')
        # ax.invert_yaxis()
        
        # Initialize plot elements
        line_stitch, = ax.plot([], [], 'b-', linewidth=2.5, label='刺绣路径', alpha=0.8)
        line_jump, = ax.plot([], [], 'r-', linewidth=2.5, label='跳针路径', alpha=0.8)
        points, = ax.plot([], [], 'ko', markersize=3, alpha=0.7)
        
        # Set title and labels
        title = dst_file.header.design_name or "DST Embroidery Animation"
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('X Coordinate', fontsize=12)
        ax.set_ylabel('Y Coordinate', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        def animate(frame):
            """Animation update function."""
            if frame >= len(coordinates):
                return line_stitch, line_jump, points
            
            # Current path
            current_path = coordinates[:frame + 1]
            
            # Separate stitch and jump segments
            stitch_x, stitch_y = [], []
            jump_x, jump_y = [], []
            
            for i in range(len(current_path) - 1):
                if i < len(dst_file.stitches) - 1:
                    # Check if this is a stitch or jump segment
                    if dst_file.stitches[i].is_stitch and dst_file.stitches[i + 1].is_stitch:
                        stitch_x.extend([current_path[i][0], current_path[i + 1][0]])
                        stitch_y.extend([current_path[i][1], current_path[i + 1][1]])
                    else:
                        jump_x.extend([current_path[i][0], current_path[i + 1][0]])
                        jump_y.extend([current_path[i][1], current_path[i + 1][1]])
            
            # Update lines
            line_stitch.set_data(stitch_x, stitch_y)
            line_jump.set_data(jump_x, jump_y)
            
            # Update points
            if current_path:
                points.set_data([p[0] for p in current_path], [p[1] for p in current_path])
            
            # Update title with progress
            ax.set_title(f'{title} - Progress: {frame + 1}/{len(coordinates)}')
            
            return line_stitch, line_jump, points
        
        # Create animation
        anim = animation.FuncAnimation(
            fig,
            animate,
            frames=len(coordinates),
            interval=frame_duration,
            blit=True,
            repeat=True
        )
        
        # Determine output path
        if output_path is None:
            base_name = dst_file.file_path or "dst_pattern"
            output_path = f"{os.path.splitext(base_name)[0]}_animation.gif"
        
        # Save animation
        print(f"Generating animation: {output_path}")
        anim.save(output_path, writer='pillow', fps=1000//frame_duration)
        print(f"Animation saved: {output_path}")
        
        if show_window:
            plt.show()
        
        plt.close()
        return output_path
    
    def create_progressive_animation(self, dst_file: DSTFile,
                                   output_path: Optional[str] = None,
                                   frame_duration: int = 300,
                                   show_window: bool = False,
                                   figsize: Tuple[int, int] = (12, 10)) -> str:
        """
        Create a progressive animation with enhanced visual effects.
        
        Args:
            dst_file: DSTFile object to animate
            output_path: Output file path (optional)
            frame_duration: Duration of each frame in milliseconds
            show_window: Whether to show the animation window
            figsize: Figure size tuple
            
        Returns:
            Path to the saved GIF file
        """
        coordinates = dst_file.get_path_coordinates()
        if not coordinates:
            raise ValueError("No coordinates found in DST file")
        
        # Set interactive backend if showing window
        if show_window:
            self.set_backend('TkAgg', interactive=True)
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Calculate bounds
        x_coords = [coord[0] for coord in coordinates]
        y_coords = [coord[1] for coord in coordinates]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Add margin
        margin = max(x_max - x_min, y_max - y_min) * 0.15
        ax.set_xlim(x_min - margin, x_max + margin)
        ax.set_ylim(y_min - margin, y_max + margin)
        
        # Set aspect ratio and invert Y axis
        ax.set_aspect('equal')
        # ax.invert_yaxis()
        
        # Initialize plot elements
        line_stitch, = ax.plot([], [], 'b-', linewidth=2.5, label='刺绣路径', alpha=0.8)
        line_jump, = ax.plot([], [], 'r-', linewidth=2.5, label='跳针路径', alpha=0.8)
        current_point, = ax.plot([], [], 'go', markersize=8, label='当前位置')
        completed_points, = ax.plot([], [], 'ko', markersize=4, alpha=0.6, label='已完成点')
        
        # Set title and labels
        title = dst_file.header.design_name or "DST Embroidery Pattern"
        ax.set_title('刺绣路径绘制过程', fontsize=16, fontweight='bold')
        ax.set_xlabel('X Coordinate', fontsize=12)
        ax.set_ylabel('Y Coordinate', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        
        # Add statistics text box
        stats_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                           verticalalignment='top', fontsize=10,
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        def animate_progressive(frame):
            """Progressive animation update function."""
            if frame >= len(coordinates):
                return line_stitch, line_jump, current_point, completed_points
            
            # Current progress
            progress = frame + 1
            total = len(coordinates)
            
            # Current path
            current_path = coordinates[:progress]
            
            # Separate stitch and jump segments
            stitch_segments = []
            jump_segments = []
            
            for i in range(len(current_path) - 1):
                if i < len(dst_file.stitches) - 1:
                    segment = [current_path[i], current_path[i + 1]]
                    if dst_file.stitches[i].is_stitch and dst_file.stitches[i + 1].is_stitch:
                        stitch_segments.append(segment)
                    else:
                        jump_segments.append(segment)
            
            # Draw stitch segments
            if stitch_segments:
                stitch_x = []
                stitch_y = []
                for segment in stitch_segments:
                    stitch_x.extend([segment[0][0], segment[1][0]])
                    stitch_y.extend([segment[0][1], segment[1][1]])
                line_stitch.set_data(stitch_x, stitch_y)
            else:
                line_stitch.set_data([], [])
            
            # Draw jump segments
            if jump_segments:
                jump_x = []
                jump_y = []
                for segment in jump_segments:
                    jump_x.extend([segment[0][0], segment[1][0]])
                    jump_y.extend([segment[0][1], segment[1][1]])
                line_jump.set_data(jump_x, jump_y)
            else:
                line_jump.set_data([], [])
            
            # Update points
            if current_path:
                completed_points.set_data([p[0] for p in current_path[:-1]],
                                        [p[1] for p in current_path[:-1]])
                current_point.set_data([current_path[-1][0]], [current_path[-1][1]])
            
            # Update statistics
            stitch_count = sum(1 for i in range(len(current_path)-1)
                             if i < len(dst_file.stitches)-1 and
                             dst_file.stitches[i].is_stitch and dst_file.stitches[i+1].is_stitch)
            jump_count = sum(1 for i in range(len(current_path)-1)
                           if i < len(dst_file.stitches)-1 and
                           not (dst_file.stitches[i].is_stitch and dst_file.stitches[i+1].is_stitch))
            
            stats_text.set_text(f'Progress: {progress}/{total}\n'
                              f'Stitch Segments: {stitch_count}\n'
                              f'Jump Segments: {jump_count}\n'
                              f'Completion: {progress/total*100:.1f}%')
            
            return line_stitch, line_jump, current_point, completed_points
        
        # Create animation
        anim = animation.FuncAnimation(
            fig,
            animate_progressive,
            frames=len(coordinates),
            interval=frame_duration,
            blit=True,
            repeat=True
        )
        
        # Determine output path
        if output_path is None:
            base_name = dst_file.file_path or "dst_pattern"
            output_path = f"{os.path.splitext(base_name)[0]}_progressive.gif"
        
        # Save animation
        print(f"Generating progressive animation: {output_path}")
        anim.save(output_path, writer='pillow', fps=1000//frame_duration)
        print(f"Progressive animation saved: {output_path}")
        
        if show_window:
            plt.show()
        
        plt.close()
        return output_path
    
    def generate_all_visualizations(self, dst_file: DSTFile,
                                   output_prefix: Optional[str] = None) -> dict:
        """
        Generate all types of visualizations for a DST file.
        
        Args:
            dst_file: DSTFile object to visualize
            output_prefix: Prefix for output files (optional)
            
        Returns:
            Dictionary with paths to generated files
        """
        if output_prefix is None:
            base_name = dst_file.file_path or "dst_pattern"
            output_prefix = os.path.splitext(base_name)[0]
        
        results = {}
        
        try:
            # Generate static image
            static_file = f"{output_prefix}_static.png"
            results['static'] = self.create_static_plot(dst_file, static_file)
            
            # Generate basic animation
            animation_file = f"{output_prefix}_animation.gif"
            results['animation'] = self.create_animation(dst_file, animation_file, frame_duration=200)
            
            # Generate progressive animation
            progressive_file = f"{output_prefix}_progressive.gif"
            results['progressive'] = self.create_progressive_animation(dst_file, progressive_file, frame_duration=300)
            
            print("All visualizations generated successfully!")
            
        except Exception as e:
            print(f"Error generating visualizations: {e}")
            raise
        
        return results
