import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QComboBox
from PyQt5.QtSerialPort import QSerialPort
import pyqtgraph as pg
import csv

class CircularBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = np.zeros(capacity)
        self.index = 0
        self.full = False

    def push(self, value):
        self.buffer[self.index] = value
        self.index = (self.index + 1) % self.capacity
        if self.index == 0:
            self.full = True

    def get_data(self):
        if self.full:
            return np.concatenate((self.buffer[self.index:], self.buffer[:self.index]))
        else:
            return self.buffer[:self.index]

class SerialPlotterWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-TIme Py Serial Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground("#000000")
        self.graph_widget.showGrid(True, True)
        self.graph_widget.setLabel("left", "Values")
        self.graph_widget.setLabel("bottom", "Time")
        self.graph_widget.setMouseEnabled(x=True, y=False)
        self.graph_widget.setClipToView(True)

        graph_widget_item = QWidget()
        graph_widget_layout = QVBoxLayout()
        graph_widget_layout.addWidget(self.graph_widget)
        graph_widget_item.setLayout(graph_widget_layout)
        self.setCentralWidget(graph_widget_item)

        self.sensor_data = {}

        self.buffer_sizes = [1000, 3000, 5000, 7000, 10000]
        self.buffer_capacity = self.buffer_sizes[0]

        self.buffer_size_combo = QComboBox()
        self.buffer_size_combo.addItems([str(size) for size in self.buffer_sizes])
        self.buffer_size_combo.setCurrentIndex(0)
        self.buffer_size_combo.currentIndexChanged.connect(self.change_buffer_size)

        graph_widget_layout.addWidget(self.buffer_size_combo)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.on_pause_clicked)
        graph_widget_layout.addWidget(self.pause_button)

        self.resume_button = QPushButton("Resume")
        self.resume_button.clicked.connect(self.resume_updates)
        graph_widget_layout.addWidget(self.resume_button)
        self.resume_button.setEnabled(False)

        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.export_data)
        graph_widget_layout.addWidget(self.export_button)
        self.export_button.setEnabled(False)

        self.serial_port = QSerialPort()
        self.serial_port.setPortName("/dev/ttyACM0")
        self.serial_port.setBaudRate(500000)
        self.serial_port.readyRead.connect(self.receive_serial_data)

        self.is_paused = False
        self.data_records = []

    def add_sensor(self, name, color):
        self.sensor_data[name] = {
            'buffer': CircularBuffer(self.buffer_capacity),
            'plot_item': self.graph_widget.plot(pen=pg.mkPen(color, width=2), name=name),
        }

    def change_buffer_size(self, index):
        self.buffer_capacity = self.buffer_sizes[index]
        for sensor in self.sensor_data.values():
            sensor['buffer'] = CircularBuffer(self.buffer_capacity)

    def on_pause_clicked(self):
        self.pause_updates()
        self.export_button.setEnabled(True)

    def pause_updates(self):
        self.is_paused = True
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(True)

    def resume_updates(self):
        self.is_paused = False
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.export_button.setEnabled(False)

    def export_data(self):
        if len(self.data_records) > 0:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Data", "", "CSV Files (*.csv)")
            if filename:
                try:
                    with open(filename, "w", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow(["Sensor", "Value"])
                        writer.writerows(self.data_records)
                    QMessageBox.information(
                        self, "Export Success", "Data exported successfully.")
                except Exception as e:
                    QMessageBox.warning(
                        self, "Export Error", f"Failed to export data: {str(e)}")
            else:
                QMessageBox.warning(self, "Export Error", "Invalid filename.")
        else:
            QMessageBox.warning(self, "Export Error", "No data to export.")

    def receive_serial_data(self):
        while self.serial_port.canReadLine():
            try:
                data = self.serial_port.readLine().data().decode("utf-8").strip()
                values = data.split(",")
                for value in values:
                    sensor_data = value.split(":")
                    sensor_name = sensor_data[0].strip()
                    sensor_value = float(sensor_data[1].strip())
                    if sensor_name in self.sensor_data and not self.is_paused:
                        data_buffer = self.sensor_data[sensor_name]['buffer']
                        data_buffer.push(sensor_value)
                        self.sensor_data[sensor_name]['plot_item'].setData(data_buffer.get_data())
                        self.data_records.append([sensor_name, sensor_value])
            except (UnicodeDecodeError, IndexError, ValueError):
                pass

if __name__ == "__main__":
    app = QApplication(sys.argv)

    plotter_window = SerialPlotterWindow()
    plotter_window.add_sensor("ADC1", 'r')
    plotter_window.add_sensor("ADC2", 'g')
    plotter_window.add_sensor("ADC3", 'b')
    plotter_window.add_sensor("ADC4", 'y')
    plotter_window.add_sensor("ADC5", 'm')

    if plotter_window.serial_port.open(QSerialPort.ReadWrite):
        plotter_window.show()
        sys.exit(app.exec_())
    else:
        print("Failed to open serial port.")
        sys.exit(1)

