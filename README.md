# System Resource Monitor for Windows

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![AMD GPU](https://img.shields.io/badge/GPU-AMD%20Radeon%20-red)  

A lightweight, always-on-top system monitoring widget for Windows 11. Monitor CPU, RAM, GPU, temperatures, and disk activity in real-time while running virtual machines, gaming, or any intensive tasks.

## Features

- Real-time monitoring of CPU, RAM, GPU, and temperatures
- Always-on-top draggable window
- Color-coded warnings for high usage (green → orange → red)
- AMD GPU support (Radeon 500 series and newer)
- Disk activity indicators
- Non-blocking updates (won't freeze your system)
- Minimal resource usage

## Installation

### Quick Start

1. **Download the repository** by clicking the "Code" button and selecting "Download ZIP", or clone it using Git:
```bash
git clone https://github.com/ThiagoMaria-SecurityIT/windows-system-monitor.git
cd system-monitor
```

2. **Set up a virtual environment (recommended)**:
```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Linux/Mac)
source venv/bin/activate
```

3. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the monitor**:
```bash
python system_monitor.py
```

### Requirements

- Windows 10/11
- Python 3.7 or newer
- AMD GPU (Radeon series) for GPU monitoring

### Optional: Temperature Monitoring

For accurate temperature readings:
1. Download [OpenHardwareMonitor](https://openhardwaremonitor.org/)
2. Run it as Administrator
3. Keep it running in the background

## Usage

- **Move the window**: Click and drag the title bar
- **Close**: Press `ESC` key or click the `✕` button
- **Position**: Place anywhere on screen (stays on top of other windows)

### Perfect for Virtual Machines

Ideal for monitoring resource usage while running QEMU/KVM virtual machines:
- Track resource allocation in real-time
- Monitor temperatures during heavy loads
- Prevent overheating by watching color warnings

## Project Challenges & Solutions

**1. UI Freezing During Updates**
Initially, the application experienced UI freezing every 2 seconds because data collection ran in the main thread. This blocked the user interface during updates, making the window unresponsive.

**Solution**: Implemented a producer-consumer threading pattern:
- Worker thread handles resource-intensive monitoring
- Queue provides thread-safe data exchange
- Main thread stays responsive with non-blocking updates

**2. Temperature Display Layout Issues**
The temperature values were being cut off in the display due to insufficient space in the layout.

**Solution**: Adjusted the widget widths dynamically (Python code line 196):
```python
value_label_width = 13 if name == 'TEMP' else 8  # Extra space for temperature values
```

**3. AMD GPU Monitoring on Windows**
AMD doesn't provide official Python bindings for Windows, making GPU monitoring challenging.

**Solution**: Implemented multiple fallback methods:
1. Primary: OpenHardwareMonitor integration
2. Fallback: pyadl library (if drivers support it)
3. Estimation: CPU-based estimation as last resort

## Project Structure

```
system-monitor/
├── system_monitor.py     # Main Python application
├── requirements.txt      # Dependencies: psutil, pywin32, wmi, pyadl
├── README.md             # Documentation 
├── LICENSE               # MIT License
├── venv/                 # Virtual environment
└── .gitignore            # To exclude the virtual environment and other temporary files  
```

## Dependencies

The project requires these Python packages (automatically installed via requirements.txt):

- `psutil==5.9.0` - System monitoring (CPU, RAM, disks)
- `pywin32==306` - Windows API integration
- `wmi==1.5.1` - Windows Management Instrumentation
- `pyadl==1.2.1` - AMD GPU monitoring (optional, fallback)  

## Contributing

Contributions are welcome to improve this project. Here's how you can help:

### Option 1: Fork and Pull Request
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -m 'Add improvement'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Open a Pull Request

### Option 2: Contact the Developer
If you have suggestions but don't want to submit code, feel free to:
- Open an issue on GitHub
- Contact me directly with your ideas

### Areas for Contribution
- Additional monitoring metrics
- Improved UI/UX
- Performance optimizations
- Better AMD/NVIDIA GPU support
- Additional platform compatibility

## Development Notes

This project demonstrates several key software engineering principles:

1. **Responsive UI Design**: Threading implementation prevents UI freezing
2. **Robust Error Handling**: Multiple fallback methods for hardware monitoring
3. **User-Centric Layout**: Dynamic widget sizing based on content needs
4. **Minimal Dependencies**: Lightweight footprint for system resources

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## AI Transparency & Development

This application was developed through collaboration between human developer and DeepSeek (AI assistant). The development process involved:

1. **Initial Requirements**: I specified for the AI DeepSeek the need for a lightweight, always-on-top monitor for QEMU virtual machine management
2. **Iterative Development**: Multiple code revisions based on real-world testing
3. **Problem Solving**: Addressing specific challenges like UI freezing and layout issues
4. **Documentation**: Creating comprehensive user and technical documentation

Key technical decisions were made collaboratively, with the AI providing code implementations and the human developer testing, providing feedback, and validating functionality on real hardware.

---

*Last updated: January 27, 2026*
