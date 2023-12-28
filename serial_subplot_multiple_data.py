import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QPushButton, QMessageBox, QVBoxLayout, QFileDialog, QComboBox
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtGui import QFont
import pyqtgraph as pg
import csv
import signal

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

        self.setWindowTitle("Real-Time Py Serial Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QGridLayout()

        self.graph_widgets = []
        self.data_buffers = []
        self.plot_data_items = []
        self.sample_index = 0
        self.data_records = []

        self.buffer_sizes = [1000, 3000, 5000, 7000, 10000]
        self.buffer_capacity = self.buffer_sizes[0]

        self.serial_port = QSerialPort()
        self.serial_port.setPortName("/dev/ttyACM0")
        self.serial_port.setBaudRate(115200)
        self.serial_port.readyRead.connect(self.receive_serial_data)

    def add_graph(self, name, x_label, y_label, row, col, color):
        graph_widget = pg.PlotWidget()
        graph_widget.setBackground("#000000")
        graph_widget.showGrid(True, True)
        graph_widget.setLabel("left", y_label)
        graph_widget.setLabel("bottom", x_label)
        graph_widget.setMouseEnabled(x=True, y=False)
        graph_widget.setClipToView(True)

        graph_widget_item = QWidget()
        graph_widget_layout = QVBoxLayout()
        graph_widget_layout.addWidget(graph_widget)
        graph_widget_item.setLayout(graph_widget_layout)
        self.layout.addWidget(graph_widget_item, row, col)

        data_buffer = CircularBuffer(self.buffer_capacity)
        plot_data_item = graph_widget.plot(data_buffer.get_data(), pen=pg.mkPen(color, width=2))

        self.data_buffers.append(data_buffer)
        self.plot_data_items.append(plot_data_item)

        self.graph_widgets.append(graph_widget)

    def receive_serial_data(self):
        while self.serial_port.canReadLine():
            try:
                data = self.serial_port.readLine().data().decode("utf-8").strip()
                values = data.split(",")
                for i, value in enumerate(values):
                    sensor_data = value.split(":")
                    sensor_name = sensor_data[0].strip()
                    sensor_value = float(sensor_data[1].strip())
                    if sensor_name in ["T", "V", "I", "P"]:
                        data_buffer = self.data_buffers[i]
                        data_buffer.push(sensor_value)
                        self.plot_data_items[i].setData(data_buffer.get_data())
                        self.data_records.append([sensor_name, sensor_value])
            except (UnicodeDecodeError, IndexError, ValueError):
                pass

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
                except Exception:
                    QMessageBox.warning(
                        self, "Export Error", "Failed to export data.")
            else:
                QMessageBox.warning(self, "Export Error", "Invalid filename.")
        else:
            QMessageBox.warning(self, "Export Error", "No data to export.")

    def change_buffer_size(self, index):
        self.buffer_capacity = self.buffer_sizes[index]
        self.data_buffers = [CircularBuffer(self.buffer_capacity) for _ in range(len(self.data_buffers))]

    def closeEvent(self, event):
        self.serial_port.close()
        event.accept()

def keyboard_interrupt_handler(signal, frame):
    sys.exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    signal.signal(signal.SIGINT, keyboard_interrupt_handler)

    app.setStyleSheet("""
        QMainWindow {
            background-color: #050505;
        }
        
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #45a049;
            cursor: pointer;
        }
        
        QLabel {
            font-size: 12px;
            font-weight: bold;
        }
        
        QComboBox {
            padding: 4px;
            font-size: 12px;
        }
    """)

    plotter_window = SerialPlotterWindow()
    plotter_window.add_graph("ADC1", "Time", "-", 1, 1, "m")
    plotter_window.add_graph("ADC2", "Time", "-", 0, 0, "y")
    plotter_window.add_graph("ADC3", "Time", "-", 0, 1, "c")
    plotter_window.add_graph("ADC4", "Time", "-", 1, 0, "c")

    buffer_size_combo = QComboBox()
    buffer_size_combo.addItems([str(size) for size in plotter_window.buffer_sizes])
    buffer_size_combo.setCurrentIndex(0)
    buffer_size_combo.currentIndexChanged.connect(plotter_window.change_buffer_size)
    plotter_window.layout.addWidget(buffer_size_combo, 2, 0, 1, 1)

    export_button = QPushButton("Export Data")
    export_button.clicked.connect(plotter_window.export_data)
    plotter_window.layout.addWidget(export_button, 2, 1, 1, 1)

    if plotter_window.serial_port.open(QSerialPort.ReadWrite):
        main_widget = QWidget()
        main_widget.setLayout(plotter_window.layout)
        plotter_window.setCentralWidget(main_widget)
        plotter_window.show()
        sys.exit(app.exec_())
    else:
        print("Failed to open serial port.")
        sys.exit(1)
