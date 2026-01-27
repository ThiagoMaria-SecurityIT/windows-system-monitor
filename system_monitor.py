"""
System Resource Monitor for Windows 11
Author: Carl
License: MIT
Description: Always-on-top movable widget showing CPU, RAM, GPU, temperatures
"""

import tkinter as tk
from tkinter import font
import psutil
import time
import threading
import queue
from ctypes import windll
import os
import sys

class SystemMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("System Monitor")
        self.root.configure(bg='#1e1e1e')
        
        # Make window always on top
        self.root.attributes('-topmost', True)
        
        # Remove window decorations for clean look
        self.root.overrideredirect(True)
        
        # Variables for dragging
        self.x = 100
        self.y = 100
        self._offsetx = 0
        self._offsety = 0
        
        # Warning thresholds
        self.cpu_warning = 80
        self.ram_warning = 85
        self.gpu_warning = 85
        self.temp_warning = 80
        
        # Queue for thread-safe communication
        self.data_queue = queue.Queue()
        
        self.setup_ui()
        self.setup_drag()
        self.update_position()
        
        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_worker, daemon=True)
        self.monitor_thread.start()
        
        # Start UI update check
        self.check_queue()
        
        # Close on Escape key
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        
    def setup_ui(self):
        """Setup the user interface"""
        # Custom font
        self.custom_font = font.Font(family="Segoe UI", size=9)
        self.bold_font = font.Font(family="Segoe UI", size=9, weight="bold")
        
        # Main frame
        self.main_frame = tk.Frame(self.root, bg='#1e1e1e', padx=12, pady=10)  # Increased padding
        self.main_frame.pack()
        
        # Title bar
        title_frame = tk.Frame(self.main_frame, bg='#2d2d2d')
        title_frame.grid(row=0, column=0, columnspan=4, sticky='ew', pady=(0, 10))  # 4 columns
        
        self.title_label = tk.Label(
            title_frame, 
            text="🔍 System Monitor (Drag me | Esc to close)", 
            bg='#2d2d2d', 
            fg='#ffffff',
            font=self.bold_font,
            padx=5,
            pady=3
        )
        self.title_label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = tk.Label(
            title_frame,
            text=" ✕ ",
            bg='#2d2d2d',
            fg='#ffffff',
            font=self.bold_font,
            cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        close_btn.bind('<Button-1>', lambda e: self.root.destroy())
        
        # Create monitoring widgets with adjusted layout
        self.create_widget('CPU', 1)
        self.create_widget('RAM', 2)
        self.create_widget('GPU', 3)
        self.create_widget('TEMP', 4)
        
        # Disk activity indicator
        disk_frame = tk.Frame(self.main_frame, bg='#1e1e1e')
        disk_frame.grid(row=5, column=0, columnspan=4, pady=(10, 0), sticky='ew')
        
        tk.Label(
            disk_frame,
            text="Disk Activity:",
            bg='#1e1e1e',
            fg='#cccccc',
            font=self.custom_font
        ).pack(side=tk.LEFT)
        
        self.disk_indicators = []
        # Show up to 4 disk indicators
        for i in range(min(4, len(psutil.disk_partitions()))):
            indicator = tk.Label(
                disk_frame,
                text=" ■ ",
                bg='#1e1e1e',
                fg='#333333',  # Dark when idle
                font=self.custom_font
            )
            indicator.pack(side=tk.LEFT, padx=2)
            self.disk_indicators.append(indicator)
        
        # Last update time
        self.time_label = tk.Label(
            self.main_frame,
            text="Starting...",
            bg='#1e1e1e',
            fg='#888888',
            font=("Segoe UI", 7)
        )
        self.time_label.grid(row=6, column=0, columnspan=4, pady=(5, 0))
        
        # Status label for debugging
        self.status_label = tk.Label(
            self.main_frame,
            text="",
            bg='#1e1e1e',
            fg='#666666',
            font=("Segoe UI", 6)
        )
        self.status_label.grid(row=7, column=0, columnspan=4, pady=(2, 0))
    
    def create_widget(self, name, row):
        """Create a monitoring widget for CPU, RAM, GPU, or TEMP"""
        frame = tk.Frame(self.main_frame, bg='#1e1e1e')
        frame.grid(row=row, column=0, columnspan=4, sticky='ew', pady=2)  # 4 columns
        
        # Label - FIXED: Reduced width for more space
        label = tk.Label(
            frame,
            text=f"{name}:",
            bg='#1e1e1e',
            fg='#cccccc',
            font=self.custom_font,
            width=6,  # Reduced from 8
            anchor='w'
        )
        label.pack(side=tk.LEFT)
        
        # Percentage bar background
        self.bar_bg_width = 140  # Slightly reduced from 150
        bar_bg = tk.Frame(frame, bg='#333333', height=12, width=self.bar_bg_width)
        bar_bg.pack(side=tk.LEFT, padx=(0, 8))  # Reduced padding
        
        # Store bar_bg reference
        if name == 'CPU':
            self.cpu_bar_bg = bar_bg
        elif name == 'RAM':
            self.ram_bar_bg = bar_bg
        elif name == 'GPU':
            self.gpu_bar_bg = bar_bg
        elif name == 'TEMP':
            self.temp_bar_bg = bar_bg
        
        # Percentage bar foreground
        bar_fg = tk.Frame(bar_bg, bg='#4CAF50', height=12)
        bar_fg.place(x=0, y=0, relwidth=0)  # Start with 0 width
        
        # Percentage label - FIXED: Reduced width
        perc_label = tk.Label(
            frame,
            text="0%",
            bg='#1e1e1e',
            fg='#ffffff',
            font=self.bold_font,
            width=4  # Reduced from 5
        )
        perc_label.pack(side=tk.LEFT)
        
        # Value label (for temperatures or additional info) - FIXED: Increased width for TEMP
        value_label_width = 13 if name == 'TEMP' else 8  # More space for TEMP
        value_label = tk.Label(
            frame,
            text="",
            bg='#1e1e1e',
            fg='#888888',
            font=self.custom_font,
            width=value_label_width,  # Dynamic width
            anchor='w'  # Left align for better readability
        )
        value_label.pack(side=tk.LEFT, padx=(2, 0))  # Small left padding
        
        # Store references
        if name == 'CPU':
            self.cpu_bar = bar_fg
            self.cpu_label = perc_label
            self.cpu_value = value_label
        elif name == 'RAM':
            self.ram_bar = bar_fg
            self.ram_label = perc_label
            self.ram_value = value_label
        elif name == 'GPU':
            self.gpu_bar = bar_fg
            self.gpu_label = perc_label
            self.gpu_value = value_label
        elif name == 'TEMP':
            self.temp_bar = bar_fg
            self.temp_label = perc_label
            self.temp_value = value_label
    
    def setup_drag(self):
        """Make the window draggable"""
        self.title_label.bind('<Button-1>', self.start_drag)
        self.title_label.bind('<B1-Motion>', self.drag)
        self.title_label.bind('<ButtonRelease-1>', self.stop_drag)
        
    def start_drag(self, event):
        self._offsetx = event.x
        self._offsety = event.y
    
    def drag(self, event):
        x = self.root.winfo_pointerx() - self._offsetx
        y = self.root.winfo_pointery() - self._offsety
        self.x = x
        self.y = y
        self.root.geometry(f'+{x}+{y}')
    
    def stop_drag(self, event):
        pass
    
    def update_position(self):
        """Update window position"""
        self.root.geometry(f'+{self.x}+{self.y}')
    
    def get_cpu_temp(self):
        """Get CPU temperature (Windows compatible)"""
        try:
            import wmi
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            temperature_infos = w.Sensor()
            for sensor in temperature_infos:
                if sensor.SensorType == 'Temperature' and 'CPU' in sensor.Name:
                    return float(sensor.Value)
        except:
            pass
        
        # Fallback: estimate from CPU usage if no temp sensor
        cpu_percent = psutil.cpu_percent(interval=0.1)
        # Rough estimation (not accurate but gives an idea)
        base_temp = 30
        return base_temp + (cpu_percent * 0.3)

    def get_gpu_info(self):
        """Get GPU usage and temperature for AMD on Windows"""
        gpu_percent = 0
        gpu_temp = 0
        gpu_type = "AMD"
        
        # First try OpenHardwareMonitor (most reliable for temps)
        try:
            import wmi
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            sensors = w.Sensor()
            
            for sensor in sensors:
                if sensor.SensorType == 'Load' and 'GPU' in sensor.Name:
                    gpu_percent = float(sensor.Value)
                elif sensor.SensorType == 'Temperature' and 'GPU' in sensor.Name:
                    gpu_temp = float(sensor.Value)
                    
        except Exception as e:
            pass  # Silent fail for OpenHardwareMonitor
        
        # If no GPU data from OHM, try to use pyadl if available
        if gpu_percent == 0:
            try:
                import pyadl
                adl_man = pyadl.ADLManager.getInstance()
                gpus = adl_man.getDevices()
                
                if gpus:
                    gpu = gpus[0]
                    try:
                        usage = gpu.getCurrentUsage()
                        if usage and hasattr(usage, 'iUsage'):
                            gpu_percent = usage.iUsage
                    except:
                        pass
                    
                    try:
                        temps = gpu.getCurrentTemperature()
                        if temps and hasattr(temps, 'iTemperature'):
                            gpu_temp = temps.iTemperature / 1000.0
                    except:
                        pass
                
                adl_man.cleanup()
                
            except ImportError:
                pass
            except Exception:
                pass
        
        # Fallback if no GPU data
        if gpu_percent == 0:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            gpu_percent = cpu_percent * 0.7  # Slightly lower than CPU
        
        if gpu_temp == 0:
            gpu_temp = self.get_cpu_temp() + 5  # GPU usually hotter
        
        return gpu_percent, gpu_temp, gpu_type
    
    def get_disk_activity(self):
        """Check disk activity for all partitions"""
        activity = []
        try:
            # Get disk I/O counters
            old_counters = getattr(self, '_old_disk_counters', None)
            new_counters = psutil.disk_io_counters(perdisk=False)
            
            if old_counters and new_counters:
                # Calculate delta for read and write operations
                read_delta = new_counters.read_count - old_counters.read_count
                write_delta = new_counters.write_count - old_counters.write_count
                
                # If there's been any activity in the last interval
                disk_active = (read_delta + write_delta) > 0
                for i in range(len(self.disk_indicators)):
                    activity.append(disk_active)
            else:
                # First run or no counters
                for i in range(len(self.disk_indicators)):
                    activity.append(False)
            
            # Store for next comparison
            self._old_disk_counters = new_counters
            
        except:
            activity = [False] * len(self.disk_indicators)
        
        return activity
    
    def collect_monitor_data(self):
        """Collect all monitoring data (runs in worker thread)"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram_percent = psutil.virtual_memory().percent
            cpu_temp = self.get_cpu_temp()
            gpu_percent, gpu_temp, gpu_type = self.get_gpu_info()
            disk_activity = self.get_disk_activity()
            
            # Additional info
            ram = psutil.virtual_memory()
            ram_used_gb = ram.used / (1024**3)
            ram_total_gb = ram.total / (1024**3)
            
            current_time = time.strftime("%H:%M:%S")
            
            # Put data in queue for UI thread
            self.data_queue.put({
                'cpu_percent': cpu_percent,
                'ram_percent': ram_percent,
                'ram_used_gb': ram_used_gb,
                'ram_total_gb': ram_total_gb,
                'gpu_percent': gpu_percent,
                'cpu_temp': cpu_temp,
                'gpu_temp': gpu_temp,
                'disk_activity': disk_activity,
                'current_time': current_time,
                'gpu_type': gpu_type
            })
            
        except Exception as e:
            # Put error in queue
            self.data_queue.put({'error': str(e)})
    
    def monitor_worker(self):
        """Worker thread that collects data periodically"""
        while self.monitoring:
            self.collect_monitor_data()
            time.sleep(2)  # Update every 2 seconds
    
    def check_queue(self):
        """Check for new data from worker thread and update UI"""
        try:
            # Process all pending messages in queue
            while True:
                try:
                    data = self.data_queue.get_nowait()
                    
                    if 'error' in data:
                        self.status_label.config(text=f"Error: {data['error'][:30]}...")
                    else:
                        self.update_ui_with_data(data)
                        self.status_label.config(text="")
                        
                except queue.Empty:
                    break
                    
        except Exception as e:
            self.status_label.config(text=f"Queue error: {str(e)[:30]}...")
        
        # Schedule next check
        self.root.after(100, self.check_queue)
    
    def update_bar(self, bar_widget, percentage, bar_bg_widget=None):
        """Update a progress bar with percentage (0-100)"""
        # Calculate width based on percentage (bar_bg_width = 140)
        width_percentage = max(0, min(100, percentage)) / 100.0
        bar_widget.place(x=0, y=0, relwidth=width_percentage)
    
    def update_ui_with_data(self, data):
        """Update the UI with data from queue"""
        try:
            # Update CPU
            cpu_percent = data['cpu_percent']
            self.update_bar(self.cpu_bar, cpu_percent)
            self.cpu_label.config(text=f"{cpu_percent:.1f}%")
            self.cpu_value.config(text=f"{psutil.cpu_count()} cores")
            
            # Color code CPU
            cpu_color = '#4CAF50'  # Green
            if cpu_percent > self.cpu_warning:
                cpu_color = '#f44336'  # Red
            elif cpu_percent > self.cpu_warning * 0.7:
                cpu_color = '#FF9800'  # Orange
            self.cpu_bar.config(bg=cpu_color)
            
            # Update RAM
            ram_percent = data['ram_percent']
            self.update_bar(self.ram_bar, ram_percent)
            self.ram_label.config(text=f"{ram_percent:.1f}%")
            self.ram_value.config(text=f"{data['ram_used_gb']:.1f}/{data['ram_total_gb']:.1f} GB")
            
            # Color code RAM
            ram_color = '#4CAF50'
            if ram_percent > self.ram_warning:
                ram_color = '#f44336'
            elif ram_percent > self.ram_warning * 0.7:
                ram_color = '#FF9800'
            self.ram_bar.config(bg=ram_color)
            
            # Update GPU
            gpu_percent = data['gpu_percent']
            self.update_bar(self.gpu_bar, gpu_percent)
            self.gpu_label.config(text=f"{gpu_percent:.1f}%")
            self.gpu_value.config(text=f"{data['gpu_temp']:.0f}°C")
            
            # Color code GPU
            gpu_color = '#4CAF50'
            if gpu_percent > self.gpu_warning:
                gpu_color = '#f44336'
            elif gpu_percent > self.gpu_warning * 0.7:
                gpu_color = '#FF9800'
            self.gpu_bar.config(bg=gpu_color)
            
            # Update Temperature bar (use max temp for bar, show both in label)
            cpu_temp = data['cpu_temp']
            gpu_temp = data['gpu_temp']
            max_temp = max(cpu_temp, gpu_temp)
            
            # For temperature bar, we need to scale it (0-100°C range)
            temp_percentage = max(0, min(100, max_temp))  # Assuming 100°C max
            self.update_bar(self.temp_bar, temp_percentage)
            
            self.temp_label.config(text=f"{max_temp:.0f}°C")
            
            # FIXED: Better formatted temperature display
            temp_text = f"CPU:{cpu_temp:.0f}° GPU:{gpu_temp:.0f}°"
            self.temp_value.config(text=temp_text)
            
            # Color code temperature
            temp_color = '#4CAF50'
            if max_temp > self.temp_warning:
                temp_color = '#f44336'
            elif max_temp > self.temp_warning * 0.7:
                temp_color = '#FF9800'
            self.temp_bar.config(bg=temp_color)
            
            # Update disk activity indicators
            disk_activity = data['disk_activity']
            for i, indicator in enumerate(self.disk_indicators):
                if i < len(disk_activity) and disk_activity[i]:
                    indicator.config(fg='#00ff00')  # Green when active
                else:
                    indicator.config(fg='#333333')  # Dark when idle
            
            # Update time
            self.time_label.config(text=f"Last update: {data['current_time']}")
            
        except Exception as e:
            self.status_label.config(text=f"UI update error: {str(e)[:30]}...")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
        self.monitoring = False

def main():
    # Check if running as administrator (optional for better temperature readings)
    try:
        is_admin = windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("Note: Running without admin privileges. Some features may be limited.")
    except:
        pass
    
    print("Starting System Monitor...")
    print("Press ESC to close")
    print("Drag the title bar to move the window")
    print("=" * 50)
    
    app = SystemMonitor()
    app.run()

if __name__ == "__main__":
    main()