"""
PyQt-based GUI application for DST embroidery file visualization.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
import traceback

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QProgressBar, QStatusBar,
    QMenuBar, QToolBar, QAction, QLabel, QPushButton, QSlider,
    QSpinBox, QCheckBox, QComboBox, QGroupBox, QScrollArea,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QTabWidget, QTextEdit, QFrame
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QRect, QPoint, QSize,
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
)
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QIcon,
    QPalette, QLinearGradient, QRadialGradient, QPainterPath
)

from ..parser import DSTParser
from ..models import DSTFile, Stitch

def speed_to_interval(speed: int):
    """
    将速度值（1-100）映射为定时器间隔（毫秒），速度越大，间隔越小（越快）。
    采用对数映射，在对数意义上更加均匀分布。
    1对应1000ms，100对应0.01ms（理论值，实际最小1ms）。
    """
    import math
    min_speed = 1
    max_speed = 100
    min_interval = 0.01  # 理论最小值：0.01ms
    max_interval = 1000  # 最大值：1000ms

    # 防止越界
    speed = max(min_speed, min(max_speed, speed))

    # 对数插值
    log_min = math.log10(min_interval)
    log_max = math.log10(max_interval)
    log_interval = log_max + (log_min - log_max) * (speed - min_speed) / (max_speed - min_speed)
    interval = 10 ** log_interval
    
    # 实际限制：QTimer最小间隔1ms
    return max(1, int(interval))

def calculate_frame_skip(speed: int):
    """
    根据速度计算帧跳过数，配合改进的速度函数
    当间隔被限制在1ms时，通过帧跳过实现真正的超高速
    最高速度时跳过100帧（0.01ms等效间隔）
    """
    import math
    min_speed = 1
    max_speed = 100
    min_interval = 0.01  # 理论最小值：0.01ms
    max_interval = 1000  # 最大值：1000ms
    
    # 防止越界
    speed = max(min_speed, min(max_speed, speed))
    
    # 计算理论间隔
    log_min = math.log10(min_interval)
    log_max = math.log10(max_interval)
    log_interval = log_max + (log_min - log_max) * (speed - min_speed) / (max_speed - min_speed)
    theoretical_interval = 10 ** log_interval
    
    if theoretical_interval < 1:
        # 需要帧跳过来实现理论速度
        frame_skip = int(1 / theoretical_interval)
        return max(1, frame_skip)
    else:
        return 1

class DSTCanvas(QWidget):
    """Custom widget for drawing DST embroidery patterns."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dst_file: Optional[DSTFile] = None
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.show_jumps = True
        self.show_stitches = True
        self.current_frame = 0
        self.animation_mode = False
        
        # Colors
        self.stitch_color = QColor(0, 0, 255)  # Blue
        self.jump_color = QColor(255, 0, 0)    # Red
        self.current_color = QColor(0, 255, 0)  # Green
        self.background_color = QColor(255, 255, 255)  # White
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.next_frame)
        
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        
    def set_dst_file(self, dst_file: DSTFile):
        """Set the DST file to display."""
        self.dst_file = dst_file
        self.current_frame = 0
        self.fit_to_view()
        self.update()
        
    def fit_to_view(self):
        """Fit the pattern to the current view."""
        if not self.dst_file:
            return
            
        bounds = self.dst_file.get_bounds()
        if bounds[2] == bounds[0] and bounds[3] == bounds[1]:
            return
            
        # Calculate scale to fit
        widget_size = self.size()
        pattern_width = bounds[2] - bounds[0]
        pattern_height = bounds[3] - bounds[1]
        
        scale_x = (widget_size.width() - 40) / pattern_width
        scale_y = (widget_size.height() - 40) / pattern_height
        self.zoom_factor = min(scale_x, scale_y, 1.0)
        
        # Center the pattern
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        
        self.pan_offset = QPoint(
            int(widget_size.width() / 2 - center_x * self.zoom_factor),
            int(widget_size.height() / 2 - center_y * self.zoom_factor)
        )
        
        self.update()
        
    def start_animation(self, frame_duration: int = 100, speed: int = 40):
        """Start animation playback."""
        if not self.dst_file:
            return
            
        self.animation_mode = True
        self.current_frame = 0
        self.animation_speed = speed  # 保存速度信息用于帧跳过
        self.animation_timer.start(frame_duration)
        
    def stop_animation(self):
        """Stop animation playback."""
        self.animation_mode = False
        self.animation_timer.stop()
        self.update()
        
    def next_frame(self):
        """Advance to next animation frame."""
        if not self.dst_file:
            return
            
        # 使用改进的帧跳过逻辑，在对数意义上更均匀
        speed = getattr(self, 'animation_speed', 40)  # 默认速度：10ms间隔
        frame_skip = calculate_frame_skip(speed)
            
        self.current_frame += frame_skip
        if self.current_frame >= len(self.dst_file.stitches):
            self.current_frame = 0  # Loop animation
            
        self.update()
        
    def paintEvent(self, event):
        """Paint the embroidery pattern."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), self.background_color)
        
        if not self.dst_file:
            painter.setPen(QPen(QColor(128, 128, 128), 2))
            painter.drawText(self.rect(), Qt.AlignCenter, "No DST file loaded")
            return
            
        # Set up coordinate transformation
        painter.save()
        painter.translate(self.pan_offset)
        painter.scale(self.zoom_factor, self.zoom_factor)
        
        # Draw pattern
        self._draw_pattern(painter)
        
        painter.restore()
        
    def _draw_pattern(self, painter: QPainter):
        """Draw the embroidery pattern."""
        coordinates = self.dst_file.get_path_coordinates()
        if not coordinates:
            return
            
        # Draw stitches and jumps
        current_x = current_y = 0
        
        for i, stitch in enumerate(self.dst_file.stitches):
            if self.animation_mode and i > self.current_frame:
                break
                
            # Calculate absolute position
            current_x += stitch.x
            current_y += stitch.y
            
            # Draw line to previous point
            if i > 0:
                prev_coord = coordinates[i - 1]
                current_coord = (current_x, current_y)
                
                # Check if both current and previous stitches are not jumps (stitch segment)
                # This matches the original logic: blue if both stitches are not jumps, red otherwise
                prev_stitch = self.dst_file.stitches[i - 1]
                is_stitch_segment = not prev_stitch.is_jump and not stitch.is_jump
                
                if is_stitch_segment and self.show_stitches:
                    painter.setPen(QPen(self.stitch_color, 2))
                elif not is_stitch_segment and self.show_jumps:
                    painter.setPen(QPen(self.jump_color, 2, Qt.DashLine))
                else:
                    continue
                    
                painter.drawLine(
                    int(prev_coord[0]), int(prev_coord[1]),
                    int(current_coord[0]), int(current_coord[1])
                )
            
            # Draw current point
            if self.animation_mode and i == self.current_frame:
                painter.setPen(QPen(self.current_color, 3))
                painter.setBrush(QBrush(self.current_color))
                painter.drawEllipse(int(current_x) - 3, int(current_y) - 3, 6, 6)
            elif i < len(coordinates) - 1:  # Don't draw the last point as a circle
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.setBrush(QBrush(QColor(0, 0, 0)))
                painter.drawEllipse(int(current_x) - 1, int(current_y) - 1, 2, 2)
                
    def wheelEvent(self, event):
        """Handle mouse wheel zoom."""
        if not self.dst_file:
            return
            
        # Calculate zoom factor
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        
        # Get mouse position relative to widget
        mouse_pos = event.pos()
        
        # Calculate zoom
        if event.angleDelta().y() > 0:
            new_zoom = self.zoom_factor * zoom_in_factor
        else:
            new_zoom = self.zoom_factor * zoom_out_factor
            
        # Limit zoom range
        new_zoom = max(0.1, min(10.0, new_zoom))
        
        if new_zoom != self.zoom_factor:
            # Adjust pan to zoom towards mouse position
            old_zoom = self.zoom_factor
            self.zoom_factor = new_zoom
            
            # Calculate the point under the mouse before zoom
            world_pos = QPoint(
                int((mouse_pos.x() - self.pan_offset.x()) / old_zoom),
                int((mouse_pos.y() - self.pan_offset.y()) / old_zoom)
            )
            
            # Calculate new pan offset
            new_pan = QPoint(
                int(mouse_pos.x() - world_pos.x() * self.zoom_factor),
                int(mouse_pos.y() - world_pos.y() * self.zoom_factor)
            )
            
            self.pan_offset = new_pan
            self.update()
            
    def mousePressEvent(self, event):
        """Handle mouse press for panning."""
        if event.button() == Qt.LeftButton:
            self.last_pan_point = event.pos()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning."""
        if hasattr(self, 'last_pan_point') and event.buttons() & Qt.LeftButton:
            delta = event.pos() - self.last_pan_point
            self.pan_offset += delta
            self.last_pan_point = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if hasattr(self, 'last_pan_point'):
            delattr(self, 'last_pan_point')


class DSTMainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.dst_file: Optional[DSTFile] = None
        self.parser = DSTParser()
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("DST Reader - Embroidery File Viewer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create left panel (file browser and controls)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Create right panel (canvas and info)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
        
    def create_left_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # File operations group
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout(file_group)
        
        self.open_button = QPushButton("Open DST File")
        self.open_button.clicked.connect(self.open_file)
        file_layout.addWidget(self.open_button)
        
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder)
        file_layout.addWidget(self.open_folder_button)
        
        layout.addWidget(file_group)
        
        # File browser
        browser_group = QGroupBox("Files")
        browser_layout = QVBoxLayout(browser_group)
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("DST Files")
        self.file_tree.itemClicked.connect(self.on_file_selected)
        browser_layout.addWidget(self.file_tree)
        
        layout.addWidget(browser_group)
        
        # Display options
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout(display_group)
        
        self.show_stitches_check = QCheckBox("Show Stitches")
        self.show_stitches_check.setChecked(True)
        self.show_stitches_check.toggled.connect(self.update_display)
        display_layout.addWidget(self.show_stitches_check)
        
        self.show_jumps_check = QCheckBox("Show Jumps")
        self.show_jumps_check.setChecked(True)
        self.show_jumps_check.toggled.connect(self.update_display)
        display_layout.addWidget(self.show_jumps_check)
        
        layout.addWidget(display_group)
        
        # Animation controls
        anim_group = QGroupBox("Animation")
        anim_layout = QVBoxLayout(anim_group)
        
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_animation)
        anim_layout.addWidget(self.play_button)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)  # 1-100，数值越大越快
        self.speed_slider.setValue(40)  # 默认速度：10ms间隔
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(20)
        anim_layout.addWidget(QLabel("Speed:"))
        anim_layout.addWidget(self.speed_slider)
        
        layout.addWidget(anim_group)
        
        # Zoom controls
        zoom_group = QGroupBox("Zoom")
        zoom_layout = QVBoxLayout(zoom_group)
        
        self.zoom_fit_button = QPushButton("Fit to View")
        self.zoom_fit_button.clicked.connect(self.fit_to_view)
        zoom_layout.addWidget(self.zoom_fit_button)
        
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(self.zoom_in_button)
        
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(self.zoom_out_button)
        
        layout.addWidget(zoom_group)
        
        layout.addStretch()
        return panel
        
    def create_right_panel(self) -> QWidget:
        """Create the right panel with canvas and info."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Canvas tab
        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        
        self.canvas = DSTCanvas()
        canvas_layout.addWidget(self.canvas)
        
        tab_widget.addTab(canvas_widget, "Pattern View")
        
        # Info tab
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        tab_widget.addTab(info_widget, "File Information")
        
        return panel
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open DST File', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        open_folder_action = QAction('Open Folder', self)
        open_folder_action.setShortcut('Ctrl+Shift+O')
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        fit_action = QAction('Fit to View', self)
        fit_action.setShortcut('Ctrl+F')
        fit_action.triggered.connect(self.fit_to_view)
        view_menu.addAction(fit_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add toolbar actions
        toolbar.addAction('Open', self.open_file)
        toolbar.addAction('Fit', self.fit_to_view)
        toolbar.addSeparator()
        toolbar.addAction('Play', self.toggle_animation)
        
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def setup_connections(self):
        """Setup signal connections."""
        self.speed_slider.valueChanged.connect(self.update_animation_speed)
        
    def open_file(self):
        """Open a DST file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open DST File", "", "DST Files (*.dst);;All Files (*)"
        )
        
        if file_path:
            self.load_dst_file(file_path)
            
    def open_folder(self):
        """Open a folder and scan for DST files."""
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        
        if folder_path:
            self.scan_folder(folder_path)
            
    def scan_folder(self, folder_path: str):
        """Scan folder for DST files."""
        self.file_tree.clear()
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.dst'):
                        file_path = os.path.join(root, file)
                        item = QTreeWidgetItem([file])
                        item.setData(0, Qt.UserRole, file_path)
                        self.file_tree.addTopLevelItem(item)
                        
            self.status_label.setText(f"Found {self.file_tree.topLevelItemCount()} DST files")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error scanning folder: {e}")
            
    def on_file_selected(self, item: QTreeWidgetItem, column: int):
        """Handle file selection."""
        file_path = item.data(0, Qt.UserRole)
        if file_path:
            self.load_dst_file(file_path)
            
    def load_dst_file(self, file_path: str):
        """Load and display a DST file."""
        try:
            self.status_label.setText("Loading DST file...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Parse DST file
            self.dst_file = self.parser.parse_file(file_path)
            
            # Update canvas
            self.canvas.set_dst_file(self.dst_file)
            
            # Update info display
            self.update_file_info()
            
            # Update display options
            self.update_display()
            
            self.status_label.setText(f"Loaded: {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading DST file: {e}")
            self.status_label.setText("Error loading file")
            
        finally:
            self.progress_bar.setVisible(False)
            
    def update_file_info(self):
        """Update the file information display."""
        if not self.dst_file:
            self.info_text.clear()
            return
            
        info_text = f"""
<h2>DST File Information</h2>
<p><b>Design Name:</b> {self.dst_file.header.design_name or 'N/A'}</p>
<p><b>Stitch Count:</b> {self.dst_file.stitch_count}</p>
<p><b>Color Count:</b> {self.dst_file.header.color_count}</p>
<p><b>Dimensions:</b> {self.dst_file.header.dimensions}</p>
<p><b>Jump Count:</b> {self.dst_file.jump_count}</p>
<p><b>Regular Stitch Count:</b> {self.dst_file.regular_stitch_count}</p>
<p><b>Color Change Count:</b> {self.dst_file.color_change_count}</p>

<h3>Bounds</h3>
"""
        
        bounds = self.dst_file.get_bounds()
        info_text += f"<p><b>Min X:</b> {bounds[0]}</p>"
        info_text += f"<p><b>Max X:</b> {bounds[2]}</p>"
        info_text += f"<p><b>Min Y:</b> {bounds[1]}</p>"
        info_text += f"<p><b>Max Y:</b> {bounds[3]}</p>"
        info_text += f"<p><b>Width:</b> {bounds[2] - bounds[0]}</p>"
        info_text += f"<p><b>Height:</b> {bounds[3] - bounds[1]}</p>"
        
        if self.dst_file.file_path:
            file_size = os.path.getsize(self.dst_file.file_path)
            info_text += f"<p><b>File Size:</b> {file_size:,} bytes</p>"
            
        self.info_text.setHtml(info_text)
        
    def update_display(self):
        """Update display options."""
        if not self.dst_file:
            return
            
        self.canvas.show_stitches = self.show_stitches_check.isChecked()
        self.canvas.show_jumps = self.show_jumps_check.isChecked()
        self.canvas.update()
        
    def toggle_animation(self):
        """Toggle animation playback."""
        if not self.dst_file:
            return
            
        if self.canvas.animation_mode:
            self.canvas.stop_animation()
            self.play_button.setText("Play")
        else:
            speed = self.speed_slider.value()
            # 将速度值转换为定时器间隔
            interval = speed_to_interval(speed)
            self.canvas.start_animation(interval, speed)
            self.play_button.setText("Stop")
            
    def update_animation_speed(self, speed: int):
        """Update animation speed."""
        if self.canvas.animation_mode:
            interval = speed_to_interval(speed)
            self.canvas.animation_timer.setInterval(interval)
            self.canvas.animation_speed = speed  # 更新速度信息



    def fit_to_view(self):
        """Fit pattern to view."""
        self.canvas.fit_to_view()
        
    def zoom_in(self):
        """Zoom in."""
        self.canvas.zoom_factor *= 1.2
        self.canvas.update()
        
    def zoom_out(self):
        """Zoom out."""
        self.canvas.zoom_factor /= 1.2
        self.canvas.update()
        
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About DST Reader", 
                         "DST Reader v1.0\n\n"
                         "A PyQt-based application for viewing and analyzing "
                         "DST embroidery files.\n\n"
                         "Features:\n"
                         "• Interactive pattern viewing\n"
                         "• Animation playback\n"
                         "• File information display\n"
                         "• Zoom and pan controls")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("DST Reader")
    app.setApplicationVersion("1.0")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = DSTMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
