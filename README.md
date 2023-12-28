# Real-Time Serial Data Plotter

A Python application for visualizing streaming serial data in real-time scrolling plots. Useful for debugging sensors, viewing live system metrics, and capturing time-series data.

## Key Features
- Real-time plotting of streaming sensor data
- Simultaneously visualize multiple sensors
- Easily adjust plot history buffer size
- Pause/resume the data stream
- Export plots to CSV for additional analysis
- Automatically detects sensors from serial data stream
- Connects to serial ports for live data streaming

## Getting Started

### Prerequisites
Requires Python 3 and the following packages:

- PyQt5 - GUI framework
- PyQtGraph - Data visualization
- PySerial - Serial comms

```bash
pip install pyqt5 pyqtgraph pyserial
```
### Usage
- Connect a microcontroller or other serial device
- Launch the app
- Open serial port, set baud rate
- App will detect and plot incoming data streams
- Adjust plot options as needed
