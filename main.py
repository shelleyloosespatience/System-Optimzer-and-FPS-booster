#!/usr/bin/env python3
"""
Enhanced Gaming Mode System Monitor v3.0
=================================
THIS SOFTWARE IS PROVIDED AS IS WITHOUT ANY GUARENTEE FROM THE DEVELOPER : )
Features:
  - Ultra-compact design for minimal screen space usage
  - OpenGL-based accurate FPS counter
  - Multi-platform support (Linux, Windows)
  - Comprehensive hardware monitoring (CPU, RAM, GPU)
  - Intelligent auto-optimization system with animations
  - One-click memory and system optimizations
  - Swap memory management
  - Sleek transparent design with color-coded indicators
  - Enhanced network speed monitoring with directional indicators 
  - Added proper comments so people can make contributions to it :3
"""
# Credits - @me_straight.
import sys
import time
import psutil
import os
import subprocess
import threading
import shutil
import random
from PyQt5.QtCore import QCoreApplication  #for our close event, that ate my resources
from collections import defaultdict
from PyQt5.QtCore import QTimer, Qt, QPoint, QSize, QPropertyAnimation, QRect, pyqtSignal, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QOpenGLContext, QSurfaceFormat, QPainter, QPen, QBrush, QPainterPath
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
    QHBoxLayout, QTextEdit, QProgressBar, QGroupBox, QGridLayout,
    QSizeGrip, QComboBox, QStyle, QFrame, QSizePolicy, QMenu,
    QToolButton, QCheckBox, QOpenGLWidget, QMessageBox, QGraphicsOpacityEffect, QSlider
)

# We import GPU libraries - handle if not available
try:
    import GPUtil
    NVIDIA_GPU_AVAILABLE = True
except ImportError:
    NVIDIA_GPU_AVAILABLE = False

try:
    import pyamdgpuinfo
    AMD_GPU_AVAILABLE = True
except ImportError:
    AMD_GPU_AVAILABLE = False

# Check if running on Windows
IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform.startswith('linux')
IS_MAC = sys.platform == 'darwin'

# OpenGL widget for accurate FPS counting
class FPSCounter(QOpenGLWidget):
    fps_updated = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(1, 1)  # Make it tiny since it's just for counting
        self.frames = 0
        self.last_time = time.time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(0)  # Update as fast as possible
        
    def paintGL(self):
        # Just count frames, don't actually draw anything
        self.frames += 1
        current_time = time.time()
        elapsed = current_time - self.last_time
        
        if elapsed >= 0.5:  # Update FPS twice per second
            fps = self.frames / elapsed
            self.fps_updated.emit(fps)
            self.frames = 0
            self.last_time = current_time

class NetworkSpeed:
    def __init__(self):
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        self.down_speed = 0
        self.up_speed = 0
        
    def update(self):
        current_net = psutil.net_io_counters()
        current_time = time.time()
        time_diff = current_time - self.last_net_time
        
        if time_diff > 0:
            self.down_speed = (current_net.bytes_recv - self.last_net_io.bytes_recv) / time_diff
            self.up_speed = (current_net.bytes_sent - self.last_net_io.bytes_sent) / time_diff
            
            # Update for next calculation
            self.last_net_io = current_net
            self.last_net_time = current_time
            
        return {
            'down': self.down_speed,
            'up': self.up_speed,
            'total_down': current_net.bytes_recv,
            'total_up': current_net.bytes_sent
        }
        
    def get_formatted_speed(self, speed_type='down'):
        """Returns formatted network speed string"""
        speed = self.down_speed if speed_type == 'down' else self.up_speed
        
        if speed < 1024:
            return f"{speed:.1f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed/1024:.1f} KB/s"
        else:
            return f"{speed/(1024*1024):.1f} MB/s"

class BoostAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self.particles = []
        self.active = False
        self.burst_count = 0
        self.max_bursts = 3
        self.alpha = 1.0
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.setInterval(50)
        
        # Fade timer
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.fade_animation)
        self.fade_timer.setInterval(50)
        
    def start_boost(self, boost_type="memory"):
        """Start a boost animation"""
        self.boost_type = boost_type
        self.particles = []
        self.active = True
        self.burst_count = 0
        self.alpha = 1.0
        self.opacity_effect.setOpacity(1.0)
        
        # Create initial particles
        self.create_particles()
        self.timer.start()
        
    def create_particles(self):
        """Create a new burst of particles"""
        # Different colors based on boost type
        if self.boost_type == "memory":
            base_color = QColor(30, 144, 255)  # Dodger Blue
        elif self.boost_type == "cpu":
            base_color = QColor(50, 205, 50)   # Lime Green
        elif self.boost_type == "gpu":
            base_color = QColor(255, 140, 0)   # Dark Orange
        else:
            base_color = QColor(138, 43, 226)  # Purple
            
        # Create 20-30 particles in a burst
        num_particles = random.randint(20, 30)
        
        for _ in range(num_particles):
            # Random position near center
            px = self.width() / 2 + random.uniform(-10, 10)
            py = self.height() / 2 + random.uniform(-10, 10)
            
            # Random velocity (speed and direction)
            angle = random.uniform(0, 2 * 3.141592)
            speed = random.uniform(2, 8)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            
            # Random size
            size = random.uniform(3, 8)
            
            # Random color variation
            color_variation = random.uniform(-30, 30)
            r = max(0, min(255, base_color.red() + color_variation))
            g = max(0, min(255, base_color.green() + color_variation))
            b = max(0, min(255, base_color.blue() + color_variation))
            color = QColor(int(r), int(g), int(b))
            
            # Random lifetime
            lifetime = random.uniform(0.5, 1.5)
            
            self.particles.append({
                'x': px, 'y': py,
                'vx': vx, 'vy': vy,
                'size': size,
                'color': color,
                'age': 0,
                'lifetime': lifetime
            })
            
        self.burst_count += 1
        
    def update_animation(self):
        """Update particle positions and state"""
        # Update existing particles
        new_particles = []
        for p in self.particles:
            # Update position
            p['x'] += p['vx']
            p['y'] += p['vy']
            
            # Apply slight gravity and drag
            p['vy'] += 0.1
            p['vx'] *= 0.98
            p['vy'] *= 0.98
            
            # Age the particle
            p['age'] += 0.05
            
            # Keep if not too old
            if p['age'] < p['lifetime']:
                new_particles.append(p)
                
        self.particles = new_particles
        
        # Create new bursts if needed
        if len(self.particles) < 5 and self.burst_count < self.max_bursts:
            self.create_particles()
        elif len(self.particles) == 0 and self.burst_count >= self.max_bursts:
            self.timer.stop()
            self.fade_timer.start()
            
        self.update()
        
    def fade_animation(self):
        """Fade out the animation"""
        self.alpha -= 0.1
        if self.alpha <= 0:
            self.alpha = 0
            self.active = False
            self.fade_timer.stop()
            self.opacity_effect.setOpacity(0.0)
        else:
            self.opacity_effect.setOpacity(self.alpha)
        self.update()
        
    def paintEvent(self, event):
        """Draw the particles"""
        if not self.active:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for p in self.particles:
            # Calculate opacity based on age
            opacity = 1.0 - (p['age'] / p['lifetime'])
            color = QColor(p['color'])
            color.setAlphaF(opacity)
            
            # Draw the particle
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            
            size = p['size'] * (1 - p['age'] / p['lifetime'])
            painter.drawEllipse(
                QPoint(int(p['x']), int(p['y'])),
                int(size), int(size)
            )

class DirectionalSpeedIndicator(QWidget):
    def __init__(self, parent=None, direction="down"):
        super().__init__(parent)
        self.direction = direction  # "down" or "up"
        self.setFixedSize(14, 10)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create arrow path
        path = QPainterPath()
        if self.direction == "down":
            # Down arrow
            path.moveTo(7, 8)
            path.lineTo(2, 3)
            path.lineTo(12, 3)
            path.closeSubpath()
            color = QColor(0, 191, 255)  # Deep Sky Blue
        else:
            # Up arrow
            path.moveTo(7, 2)
            path.lineTo(2, 7)
            path.lineTo(12, 7)
            path.closeSubpath()
            color = QColor(255, 165, 0)  # Orange
            
        # Fill arrow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPath(path)

class AutoOptimizer:
    def __init__(self, parent):
        self.parent = parent
        self.enabled = False
        self.last_optimization = 0
        self.optimization_interval = 60  # seconds
        self.optimization_threshold = {
            'ram': 85,  # % usage
            'cpu': 90,  # % usage
            'gpu': 90   # % usage
        }
        self.optimization_types = []
        
    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
        
    def check_and_optimize(self, metrics):
        """Check if system needs optimization and perform if needed"""
        if not self.enabled:
            return None
            
        current_time = time.time()
        if current_time - self.last_optimization < self.optimization_interval:
            return None
            
        # Determine what needs optimization
        self.optimization_types = []
        
        if metrics['ram'] > self.optimization_threshold['ram']:
            self.optimization_types.append('memory')
            
        if metrics['cpu'] > self.optimization_threshold['cpu']:
            self.optimization_types.append('cpu')
            
        if metrics.get('gpu') and metrics['gpu'] > self.optimization_threshold['gpu']:
            self.optimization_types.append('gpu')
            
        # Perform optimizations if needed
        if self.optimization_types:
            self.last_optimization = current_time
            return self.perform_optimization()
        return None
        
    def perform_optimization(self):
        """Perform system optimizations"""
        # Choose the most critical type to optimize
        if not self.optimization_types:
            return None
            
        optimization_type = self.optimization_types[0]
        
        # Do different optimizations based on type
        if optimization_type == 'memory':
            self.optimize_memory()
            return 'memory'
        elif optimization_type == 'cpu':
            self.optimize_cpu()
            return 'cpu'
        elif optimization_type == 'gpu':
            self.optimize_gpu()
            return 'gpu'
        return None
        
    def optimize_memory(self):
        """Optimize memory usage"""
        # Platform-specific memory optimizations
        try:
            if IS_LINUX:
                # Try to free page cache
                commands = [
                    "sync",  # Sync filesystem first
                    "echo 1 > /proc/sys/vm/drop_caches"
                ]
                for cmd in commands:
                    try:
                        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
                    except:
                        pass
            elif IS_WINDOWS:
                # For Windows, basic memory cleanup
                try:
                    import ctypes
                    ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
                except:
                    pass
            elif IS_MAC:
                # Mac OS cache clearing (non-sudo)
                try:
                    subprocess.run("vm_stat", shell=True, stderr=subprocess.DEVNULL)
                except:
                    pass
        except:
            pass  # Silently fail if optimization doesn't work
            
    def optimize_cpu(self):
        """Optimize CPU usage"""
        # Simple CPU optimization - adjust process priorities
        try:
            if IS_WINDOWS:
                # Set current process to high priority
                try:
                    import win32process
                    import win32api
                    win32process.SetPriorityClass(win32api.GetCurrentProcess(), win32process.HIGH_PRIORITY_CLASS)
                except:
                    pass
            elif IS_LINUX:
                # Adjust nice values for background processes
                try:
                    current_pid = os.getpid()
                    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                        if proc.info['pid'] != current_pid and proc.info['cpu_percent'] > 10:
                            try:
                                p = psutil.Process(proc.info['pid'])
                                if p.nice() < 10:  # Only if not already niced
                                    p.nice(10)
                            except:
                                pass
                except:
                    pass
        except:
            pass  # Silently fail if optimization doesn't work
            
    def optimize_gpu(self):
        """Optimize GPU usage"""
        # GPU optimization is limited, but we can try to adjust application settings
        try:
            if IS_WINDOWS:
                # For NVIDIA GPUs, try to kill unnecessary GPU processes
                try:
                    for proc in psutil.process_iter(['pid', 'name']):
                        name = proc.info['name'].lower()
                        if any(x in name for x in ['nvidia', 'geforce', 'control panel']) and 'experience' in name:
                            try:
                                p = psutil.Process(proc.info['pid'])
                                p.suspend()  # Suspend instead of kill
                            except:
                                pass
                except:
                    pass
        except:
            pass  # Silently fail if optimization doesn't work

class CompactMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.offset = QPoint(0, 0)
        self.expanded = False
        self.is_admin = False
        # Fixed dimensions
        self.compact_width = 350
        self.compact_height = 60
        self.expanded_height = 450
        
        # GPU detection
        self.has_nvidia = NVIDIA_GPU_AVAILABLE
        self.has_amd = AMD_GPU_AVAILABLE
        self.has_gpu = self.has_nvidia or self.has_amd
        
        # Initialize system information
        self.cpu_count = psutil.cpu_count(logical=True)
        self.cpu_data = {}
        
        # Update speed settings
        self.update_speeds = {
            "Normal": 1000,
            "Fast": 500,
            "Ultra": 100
        }
        self.current_speed = "Normal"
        
        # Network monitor
        self.network = NetworkSpeed()
        
        # Auto-optimizer
        self.auto_optimizer = AutoOptimizer(self)
        
        # Animation components
        self.boost_animation = None
        
        # Import math for animations
        global math
        import math
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Gaming Mode System Monitor")
        # Set window flags
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set up the main layout with styling
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(6)
        
        # Style setup
        self.setFont(QFont("Segoe UI", 8))
        self.setStyleSheet("""
            QWidget {
                color: #FFFFFF;
                background-color: rgba(20, 20, 30, 180);
                border-radius: 8px;
            }
            QGroupBox {
                border: 1px solid #444444;
                border-radius: 6px;
                margin-top: 8px;
                font-weight: bold;
                background-color: rgba(35, 35, 45, 170);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
            }
            QPushButton, QToolButton {
                background-color: #3C3F5A;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QPushButton:hover, QToolButton:hover {
                background-color: #494D70;
            }
            QPushButton:pressed, QToolButton:pressed {
                background-color: #636785;
            }
            QProgressBar {
                border: 1px solid #444444;
                border-radius: 3px;
                text-align: center;
                background-color: rgba(25, 25, 35, 170);
                max-height: 6px;
                min-height: 6px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                                stop:0 #007BFF, stop:1 #6610f2);
                border-radius: 2px;
            }
            QTextEdit {
                background-color: rgba(30, 30, 40, 170);
                border: 1px solid #444444;
                border-radius: 4px;
            }
            QComboBox {
                background-color: #3C3F5A;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 12px;
                border-left-width: 1px;
                border-left-color: #555555;
                border-left-style: solid;
            }
            QLabel {
                background-color: transparent;
            }
            #compactWidget {
                background-color: rgba(20, 20, 30, 180);
                border-radius: 8px;
                border: 1px solid rgba(80, 80, 120, 120);
            }
            #miniLabel {
                font-size: 7pt;
                color: #AAA;
            }
            #fpsValue {
                font-size: 14pt;
                font-weight: bold;
                color: #FFF;
            }
            #netValue {
                font-size: 7pt;
                font-weight: bold;
                color: #8AEEEE;
            }
            QCheckBox {
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid #555555;
                border-radius: 2px;
                background-color: #2D2D40;
            }
            QCheckBox::indicator:checked {
                background-color: #3D8EC9;
            }
            #boostButton {
                background-color: #8A2BE2;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            #boostButton:hover {
                background-color: #9932CC;
            }
            #boostButton:pressed {
                background-color: #7B68EE;
            }
            #boosterActive {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
        """)
        
        # Create FPS counter (accurate OpenGL-based)
        self.fps_counter = FPSCounter(self)
        self.fps_counter.fps_updated.connect(self.update_fps)
        
        # Create compact view (always visible)
        self.compact_widget = QWidget()
        self.compact_widget.setObjectName("compactWidget")
        self.compact_widget.setFixedHeight(self.compact_height - 16)  # Accounting for margins
        compact_layout = QHBoxLayout(self.compact_widget)
        compact_layout.setContentsMargins(8, 4, 8, 4)
        compact_layout.setSpacing(8)
        
        # FPS display (main focus)
        fps_container = QVBoxLayout()
        fps_container.setSpacing(0)
        fps_label = QLabel("FPS")
        fps_label.setObjectName("miniLabel")
        fps_label.setAlignment(Qt.AlignCenter)
        self.fps_value = QLabel("0")
        self.fps_value.setObjectName("fpsValue")
        self.fps_value.setAlignment(Qt.AlignCenter)
        fps_container.addWidget(fps_label)
        fps_container.addWidget(self.fps_value)
        
        # RAM mini display
        ram_container = QVBoxLayout()
        ram_container.setSpacing(0)
        ram_label = QLabel("RAM")
        ram_label.setObjectName("miniLabel")
        ram_label.setAlignment(Qt.AlignCenter)
        self.ram_bar = QProgressBar()
        self.ram_bar.setMaximum(100)
        self.ram_bar.setValue(0)
        self.ram_bar.setTextVisible(False)
        
        # Network speed indicators initialization
        self.down_arrow = DirectionalSpeedIndicator(self, "down")
        self.up_arrow = DirectionalSpeedIndicator(self, "up")
        self.net_down_value = QLabel("0 KB/s")
        self.net_up_value = QLabel("0 KB/s")
        self.net_down_value.setObjectName("netValue")
        self.net_up_value.setObjectName("netValue")
        
        # Network speed container
        net_speed_container = QVBoxLayout()  # Changed to vertical
        net_speed_container.setSpacing(2)
        
        # Download speed
        down_container = QHBoxLayout()
        down_container.addWidget(self.down_arrow)
        down_container.addWidget(self.net_down_value)
        net_speed_container.addLayout(down_container)
        
        # Upload speed
        up_container = QHBoxLayout()
        up_container.addWidget(self.up_arrow)
        up_container.addWidget(self.net_up_value)
        net_speed_container.addLayout(up_container)
        
        # Add network container to RAM container
        ram_container.addLayout(net_speed_container)
        
        # CPU mini display
        cpu_container = QVBoxLayout()
        cpu_container.setSpacing(0)
        cpu_label = QLabel("CPU")
        cpu_label.setObjectName("miniLabel")
        cpu_label.setAlignment(Qt.AlignCenter)
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        self.cpu_bar.setValue(0)
        self.cpu_bar.setTextVisible(False)
        
        # Booster status indicator
        self.boost_status = QLabel("BOOST OFF")
        self.boost_status.setObjectName("miniLabel")
        self.boost_status.setAlignment(Qt.AlignCenter)
        
        cpu_container.addWidget(cpu_label)
        cpu_container.addWidget(self.cpu_bar)
        cpu_container.addWidget(self.boost_status)
        
        # GPU mini display (if available)
        if self.has_gpu:
            gpu_container = QVBoxLayout()
            gpu_container.setSpacing(0)
            gpu_label = QLabel("GPU")
            gpu_label.setObjectName("miniLabel")
            gpu_label.setAlignment(Qt.AlignCenter)
            self.gpu_bar = QProgressBar()
            self.gpu_bar.setMaximum(100)
            self.gpu_bar.setValue(0)
            self.gpu_bar.setTextVisible(False)
            gpu_container.addWidget(gpu_label)
            gpu_container.addWidget(self.gpu_bar)
        
        # Expand/menu button
        self.menu_btn = QToolButton()
        self.menu_btn.setText("≡")
        self.menu_btn.setToolTip("Options")
        self.menu_btn.clicked.connect(self.toggle_expanded)
        
        # Add everything to compact layout
        compact_layout.addLayout(fps_container)
        compact_layout.addLayout(ram_container)
        compact_layout.addLayout(cpu_container)
        if self.has_gpu:
            compact_layout.addLayout(gpu_container)
        compact_layout.addWidget(self.menu_btn)
        
        # Add compact widget to main layout
        self.main_layout.addWidget(self.compact_widget)
        
        # Create expandable content (hidden by default)
        self.expandable_widget = QWidget()
        self.expandable_widget.setVisible(False)
        expandable_layout = QVBoxLayout(self.expandable_widget)
        expandable_layout.setContentsMargins(6, 0, 6, 6)
        
        # Detailed system metrics
        metrics_group = QGroupBox("SYSTEM METRICS")
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(6)
        
        # CPU detailed info
        self.cpu_label = QLabel("CPU: 0.0%")
        self.cpu_detailed_label = QLabel("Core: [0.0%, 0.0%, ...]")
        self.cpu_temp_label = QLabel("CPU Temp: N/A")
        metrics_layout.addWidget(self.cpu_label, 0, 0)
        metrics_layout.addWidget(self.cpu_detailed_label, 0, 1)
        metrics_layout.addWidget(self.cpu_temp_label, 1, 0)
        
        # RAM detailed info
        self.ram_label = QLabel("RAM: 0MB / 0MB (0.0%)")
        self.ram_detailed_label = QLabel("Free: 0MB | Cached: 0MB")
        metrics_layout.addWidget(self.ram_label, 2, 0)
        metrics_layout.addWidget(self.ram_detailed_label, 2, 1)
        
        # Swap detailed info
        self.swap_label = QLabel("Swap: 0MB / 0MB (0.0%)")
        self.swap_bar = QProgressBar()
        self.swap_bar.setMaximum(100)
        metrics_layout.addWidget(self.swap_label, 3, 0)
        metrics_layout.addWidget(self.swap_bar, 3, 1)
        
        # GPU info (if available)
        if self.has_gpu:
            self.gpu_label = QLabel("GPU: 0.0%")
            self.gpu_temp_label = QLabel("GPU Temp: N/A")
            self.gpu_memory_label = QLabel("VRAM: 0MB / 0MB (0.0%)")
            metrics_layout.addWidget(self.gpu_label, 4, 0)
            metrics_layout.addWidget(self.gpu_temp_label, 4, 1)
            metrics_layout.addWidget(self.gpu_memory_label, 5, 0, 1, 2)
        
        metrics_group.setLayout(metrics_layout)
        expandable_layout.addWidget(metrics_group)
        
        # Performance Booster section (New feature replacing Network section)
        boost_group = QGroupBox("PERFORMANCE BOOSTER")
        boost_layout = QVBoxLayout()
        
        # Booster description
        boost_desc = QLabel("Automatically optimize system resources to improve gaming performance")
        boost_desc.setWordWrap(True)
        boost_layout.addWidget(boost_desc)
        
        # Booster controls
        boost_controls = QHBoxLayout()
        
        # Auto-boost toggle
        self.auto_boost_check = QCheckBox("Auto-Boost")
        self.auto_boost_check.setToolTip("Automatically optimize when resources are low")
        self.auto_boost_check.stateChanged.connect(self.toggle_auto_boost)
        
        # Manual boost button
        self.manual_boost_btn = QPushButton("BOOST NOW")
        self.manual_boost_btn.setObjectName("boostButton")
        self.manual_boost_btn.setToolTip("Manually trigger a performance boost")
        self.manual_boost_btn.clicked.connect(self.trigger_manual_boost)
        
        boost_controls.addWidget(self.auto_boost_check)
        boost_controls.addWidget(self.manual_boost_btn)
        boost_layout.addLayout(boost_controls)
        
        # Create boost animation widget
        self.boost_animation = BoostAnimation(self)
        self.boost_animation.setVisible(False)
        
        boost_group.setLayout(boost_layout)
        expandable_layout.addWidget(boost_group)
        
        # Settings section
        settings_group = QGroupBox("SETTINGS")
        settings_layout = QVBoxLayout()
        
        # Update speed
        update_speed_layout = QHBoxLayout()
        update_speed_layout.addWidget(QLabel("Update Speed:"))
        self.update_speed_combo = QComboBox()
        self.update_speed_combo.addItems(["Normal", "Fast", "Ultra"])
        self.update_speed_combo.currentTextChanged.connect(self.change_update_speed)
        update_speed_layout.addWidget(self.update_speed_combo)
        settings_layout.addLayout(update_speed_layout)
        
        # Transparency
        transparency_layout = QHBoxLayout()
        transparency_layout.addWidget(QLabel("Transparency:"))
        self.transparency_slider = QSlider(Qt.Horizontal)  # Change to QSlider
        self.transparency_slider.setMinimum(10)
        self.transparency_slider.setMaximum(100)
        self.transparency_slider.setValue(100)  # Start fully opaque
        self.transparency_slider.setToolTip("100%")
        self.transparency_slider.valueChanged.connect(self.on_transparency_changed)
        self.transparency_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2D2D40;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007BFF;
                width: 12px;
                margin: -3px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #0056b3;
            }
        """)
        transparency_layout.addWidget(self.transparency_slider)
        
        # Add percentage label
        self.transparency_label = QLabel("100%")
        self.transparency_label.setMinimumWidth(40)
        transparency_layout.addWidget(self.transparency_label)
        settings_layout.addLayout(transparency_layout)
        
        # Admin mode toggle in settings
        admin_layout = QHBoxLayout()
        self.admin_btn = QPushButton("🛡️ Enable Admin Mode")
        self.admin_btn.setObjectName("adminButton")
        self.admin_btn.clicked.connect(self.request_admin)
        admin_layout.addWidget(self.admin_btn)
        settings_layout.addLayout(admin_layout)
        
        # Close button
        close_layout = QHBoxLayout()
        self.close_btn = QPushButton("Close Monitor")
        self.close_btn.clicked.connect(self.close)
        close_layout.addStretch()
        close_layout.addWidget(self.close_btn)
        close_layout.addStretch()
        settings_layout.addLayout(close_layout)
        
        settings_group.setLayout(settings_layout)
        expandable_layout.addWidget(settings_group)
        
        # Size grip for resizing
        size_grip = QSizeGrip(self)
        size_grip_layout = QHBoxLayout()
        size_grip_layout.setContentsMargins(0, 0, 0, 0)
        size_grip_layout.addStretch()
        size_grip_layout.addWidget(size_grip)
        expandable_layout.addLayout(size_grip_layout)
        
        # Add expandable widget to main layout
        self.main_layout.addWidget(self.expandable_widget)
        
        # Set the main layout
        self.setLayout(self.main_layout)
        
        # Setup timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(self.update_speeds[self.current_speed])
        
        # Set initial size
        self.resize(self.compact_width, self.compact_height)
        self.setFixedWidth(self.compact_width)
        
        # Position at top-right of screen
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry()
        self.move(screen_rect.width() - self.width() - 20, 20)
        
        self.last_transparency = 100  # Store last transparency value
        
        # Custom styles for admin button
        self.setStyleSheet(self.styleSheet() + """
            #adminButton {
                background-color: #4a4a4a;
                color: #ddd;
                border: 1px solid #666;
            }
            #adminButton:hover {
                background-color: #5a5a5a;
            }
            #adminActive {
                background-color: #7B1FA2;
                color: white;
            }
        """)
        
    def toggle_expanded(self):
        """Toggle between compact and expanded views"""
        self.expanded = not self.expanded
        self.expandable_widget.setVisible(self.expanded)

        if self.expanded:
            self.setFixedHeight(self.expanded_height)
        else:
            self.setFixedHeight(self.compact_height)

        self.updateGeometry()
    
    def update_fps(self, fps):
        """Update FPS counter from OpenGL widget"""
        self.fps_value.setText(f"{int(fps)}")
        
        # Color-code based on performance
        if fps >= 60:
            self.fps_value.setStyleSheet("color: #00FF00;")  # Green for good
        elif fps >= 30:
            self.fps_value.setStyleSheet("color: #FFFF00;")  # Yellow for acceptable
        else:
            self.fps_value.setStyleSheet("color: #FF0000;")  # Red for poor
    
    def update_stats(self):
        """Update all system statistics"""
        # Get CPU usage
        cpu_percent = psutil.cpu_percent()
        cpu_percent_per_core = psutil.cpu_percent(percpu=True)
        
        # Format core percentages nicely
        if len(cpu_percent_per_core) > 6:
            # Only show first 4 and last core if many cores
            cores_str = f"{cpu_percent_per_core[0]:.1f}%, {cpu_percent_per_core[1]:.1f}%, {cpu_percent_per_core[2]:.1f}%, {cpu_percent_per_core[3]:.1f}%... {cpu_percent_per_core[-1]:.1f}%"
        else:
            cores_str = ", ".join([f"{p:.1f}%" for p in cpu_percent_per_core])
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used // (1024 * 1024)  # MB
        memory_total = memory.total // (1024 * 1024)  # MB
        memory_cached = memory.cached // (1024 * 1024) if hasattr(memory, 'cached') else 0  # MB
        memory_free = memory.available // (1024 * 1024)  # MB
        
        # Get swap usage
        swap = psutil.swap_memory()
        swap_percent = swap.percent
        swap_used = swap.used // (1024 * 1024)  # MB
        swap_total = swap.total // (1024 * 1024)  # MB
        
        # Get GPU usage (if available)
        gpu_percent = 0
        gpu_memory_percent = 0
        gpu_temp = 0
        gpu_memory_used = 0
        gpu_memory_total = 0
        
        if self.has_nvidia:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use first GPU
                    gpu_percent = gpu.load * 100
                    gpu_memory_percent = (gpu.memoryUsed / gpu.memoryTotal) * 100
                    gpu_temp = gpu.temperature
                    gpu_memory_used = gpu.memoryUsed
                    gpu_memory_total = gpu.memoryTotal
            except:
                pass
        elif self.has_amd:
            try:
                gpu_devices = pyamdgpuinfo.get_devices()
                if gpu_devices:
                    gpu = gpu_devices[0]  # Use first GPU
                    gpu_percent = gpu.query_load() * 100
                    gpu_memory_used = gpu.query_vram_usage()
                    gpu_memory_total = gpu.query_vram_size()
                    gpu_memory_percent = (gpu_memory_used / gpu_memory_total) * 100
                    gpu_temp = gpu.query_temperature()
            except:
                pass
        
        # Update network speeds
        net_stats = self.network.update()
        
        # Update UI elements - Compact view
        self.cpu_bar.setValue(int(cpu_percent))
        
        # Color-code progress bars based on usage levels
        if cpu_percent <= 60:
            self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")  # Green
        elif cpu_percent <= 85:
            self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")  # Yellow
        else:
            self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")  # Red
        
        self.ram_bar.setValue(int(memory_percent))
        if memory_percent <= 60:
            self.ram_bar.setStyleSheet("QProgressBar::chunk { background-color: #2196F3; }")  # Blue
        elif memory_percent <= 85:
            self.ram_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")  # Yellow
        else:
            self.ram_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")  # Red
        
        # Update network speed indicators
        self.net_down_value.setText(self.network.get_formatted_speed("down"))
        self.net_up_value.setText(self.network.get_formatted_speed("up"))
        
        if self.has_gpu:
            self.gpu_bar.setValue(int(gpu_percent))
            if gpu_percent <= 60:
                self.gpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #9C27B0; }")  # Purple
            elif gpu_percent <= 85:
                self.gpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")  # Yellow
            else:
                self.gpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")  # Red
        
        # Update detailed metrics if expanded
        if self.expanded:
            # CPU metrics
            self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")
            self.cpu_detailed_label.setText(f"Cores: [{cores_str}]")
            
            # Try to get CPU temperature if available
            try:
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        for name, entries in temps.items():
                            if any(x.lower() in name.lower() for x in ["cpu", "core", "package"]):
                                temp = entries[0].current
                                self.cpu_temp_label.setText(f"CPU Temp: {temp:.1f}°C")
                                break
            except:
                self.cpu_temp_label.setText("CPU Temp: N/A")
            
            # RAM metrics
            self.ram_label.setText(f"RAM: {memory_used:,}MB / {memory_total:,}MB")
            self.ram_detailed_label.setText(f"({memory_percent:.1f}%) | Free: {memory_free:,}MB")
            self.ram_label.setWordWrap(True)
            self.ram_detailed_label.setWordWrap(True)
            
            # Swap metrics
            self.swap_label.setText(f"Swap: {swap_used:,}MB / {swap_total:,}MB ({swap_percent:.1f}%)")
            self.swap_bar.setValue(int(swap_percent))
            
            # GPU metrics (if available)
            if self.has_gpu:
                self.gpu_label.setText(f"GPU: {gpu_percent:.1f}%")
                self.gpu_temp_label.setText(f"GPU Temp: {gpu_temp:.1f}°C")
                self.gpu_memory_label.setText(f"VRAM: {gpu_memory_used:.0f}MB / {gpu_memory_total:.0f}MB ({gpu_memory_percent:.1f}%)")
        
        # Check for auto-optimization
        if self.auto_optimizer.enabled:
            optimization_metrics = {
                'cpu': cpu_percent,
                'ram': memory_percent,
                'gpu': gpu_percent if self.has_gpu else 0
            }
            
            optimized = self.auto_optimizer.check_and_optimize(optimization_metrics)
            if optimized:
                self.show_boost_animation(optimized)
                self.boost_status.setText("AUTO BOOST")
                self.boost_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
                
                # Start a timer to reset the status after a few seconds
                QTimer.singleShot(3000, self.reset_boost_status)
    
    def reset_boost_status(self):
        """Reset the boost status indicator"""
        if self.auto_optimizer.enabled:
            self.boost_status.setText("BOOST ON")
            self.boost_status.setStyleSheet("color: #4CAF50;")
        else:
            self.boost_status.setText("BOOST OFF")
            self.boost_status.setStyleSheet("color: #AAA;")
    
    def change_update_speed(self, speed):
        """Change the update frequency"""
        self.current_speed = speed
        self.timer.setInterval(self.update_speeds[speed])
    
    def toggle_auto_boost(self, state):
        """Toggle auto-optimization on/off"""
        is_enabled = self.auto_optimizer.toggle()
        if is_enabled:
            self.boost_status.setText("BOOST ON")
            self.boost_status.setStyleSheet("color: #4CAF50;")
        else:
            self.boost_status.setText("BOOST OFF")
            self.boost_status.setStyleSheet("color: #AAA;")
    
    def trigger_manual_boost(self):
        """Manually trigger system optimization"""
        # Get current metrics for optimization
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        gpu_percent = 0
        if self.has_gpu:
            if self.has_nvidia:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]
                        gpu_percent = gpu.load * 100
                except:
                    pass
            elif self.has_amd:
                try:
                    gpu_devices = pyamdgpuinfo.get_devices()
                    if gpu_devices:
                        gpu = gpu_devices[0]
                        gpu_percent = gpu.query_load() * 100
                except:
                    pass
        
        # Set all optimization types to check  :)
        self.auto_optimizer.optimization_types = ['memory', 'cpu']
        if self.has_gpu:
            self.auto_optimizer.optimization_types.append('gpu')
            
        # Perform optimization :3
        optimized = self.auto_optimizer.perform_optimization()
        if optimized:
            self.show_boost_animation(optimized)
            
            # Update status
            self.boost_status.setText("MANUAL BOOST")
            self.boost_status.setStyleSheet("color: #FF9800; font-weight: bold;")
            
            # Reset status after 3 seconds
            QTimer.singleShot(3000, self.reset_boost_status)
    
    def show_boost_animation(self, boost_type):
        """Show the boost animation"""
        self.boost_animation.move(
            self.width() // 2 - self.boost_animation.width() // 2,
            self.height() // 2 - self.boost_animation.height() // 2
        )
        self.boost_animation.setVisible(True)
        self.boost_animation.start_boost(boost_type)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement for dragging"""
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release after dragging"""
        self.offset = None
        super().mouseReleaseEvent(event)

    def on_transparency_changed(self, value):
        """Handle transparency slider value changes"""
        opacity = value / 100.0
        self.setWindowOpacity(opacity)
        
        # Update tooltip and label
        percentage = f"{value}%"
        self.transparency_slider.setToolTip(percentage)
        self.transparency_label.setText(percentage)
        
        # Save the value for persistence (optional)
        self.last_transparency = value

    def request_admin(self):
        """Request administrator privileges"""
        try:
            if IS_WINDOWS:
                import ctypes
                if ctypes.windll.shell32.IsUserAnAdmin():
                    self.is_admin = True
                    self.admin_btn.setText("🛡️ Admin Mode Active")
                    self.admin_btn.setObjectName("adminActive")
                    return
                    
                # Request elevation
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit()
                
            elif IS_LINUX:
                import subprocess
                result = subprocess.run(['pkexec', 'echo', 'Admin access granted'], 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    self.is_admin = True
                    self.admin_btn.setText("🛡️ Admin Mode Active")
                    self.admin_btn.setObjectName("adminActive")
                    
            self.enhance_optimizations()
            
        except Exception as e:
            QMessageBox.warning(self, "Admin Rights", 
                              "Failed to obtain admin rights: " + str(e))

    def enhance_optimizations(self):
        """Enhanced optimization methods when running as admin"""
        if not self.is_admin:
            return

        if IS_WINDOWS:
            try:
                # Set process priority
                import win32api, win32process, win32con
                handle = win32api.GetCurrentProcess()
                win32process.SetPriorityClass(handle, win32process.HIGH_PRIORITY_CLASS)
                
                # Additional Windows optimizations
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", 
                                   0, winreg.KEY_ALL_ACCESS)
                winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
            except:
                pass

        elif IS_LINUX:
            try:
                # Set process priority
                import os
                os.nice(-20)
                
                # Additional Linux optimizations
                commands = [
                    "echo 3 > /proc/sys/vm/drop_caches",
                    "echo 1 > /proc/sys/vm/compact_memory",
                    "sysctl -w vm.swappiness=10"
                ]
                for cmd in commands:
                    try:
                        subprocess.run(['pkexec', 'sh', '-c', cmd], 
                                    stderr=subprocess.DEVNULL)
                    except:
                        pass
            except:
                pass

    def optimize_memory(self):
        """Enhanced memory optimization with admin privileges"""
        if self.is_admin:
            if IS_WINDOWS:
                try:
                    # Enhanced Windows memory optimization
                    import ctypes
                    ctypes.windll.psapi.EmptyWorkingSet(-1)  # All processes
                    os.system("powershell -Command \"Get-Process | Stop-Process -Force\"")
                except:
                    pass
            elif IS_LINUX:
                try:
                    # Enhanced Linux memory optimization
                    commands = [
                        "sync",
                        "echo 3 > /proc/sys/vm/drop_caches",
                        "echo 1 > /proc/sys/vm/compact_memory",
                        "swapoff -a && swapon -a"
                    ]
                    for cmd in commands:
                        subprocess.run(['pkexec', 'sh', '-c', cmd], 
                                    stderr=subprocess.DEVNULL)
                except:
                    pass
        else:
            super().optimize_memory()

    def closeEvent(self, event):
        # This will be triggered when the widget is closed.
        print("closeEvent triggered, shutting down the process!")
        import os
        os._exit(0)  # Forcefully kills the process
# # #Our close event was outside of the scope, fully kill the instance fr, this shit ate my ram for several minutes until i realized



# def closeEvent(self, event):
#     print("closeEvent triggered")
#     import os
#     os._exit(0)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for consistent cross-platform look
    
    # Create window
    window = CompactMonitor()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
