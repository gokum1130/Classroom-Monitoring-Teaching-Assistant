import sys
import cv2
import numpy as np
import zmq
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QLineEdit, QMessageBox, QSlider
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from cryptography.fernet import Fernet
import pyautogui
import threading
import json
import random
import string
import time

class ServerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teacher's Console")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize session code
        self.session_code = None  # Will be set by monitor
        
        # Initialize encryption
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        
        # Initialize ZMQ context
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:5556")
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # Control panel
        control_panel = QWidget()
        control_layout = QVBoxLayout()
        
        # Session code input
        code_input_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter Lab Code from Monitor")
        self.code_input.setMaxLength(6)
        self.code_input.textChanged.connect(self.update_session_code)
        
        set_code_button = QPushButton("Set Code")
        set_code_button.clicked.connect(self.set_session_code)
        
        code_input_layout.addWidget(self.code_input)
        code_input_layout.addWidget(set_code_button)
        control_layout.addLayout(code_input_layout)
        
        # Session code display
        self.session_label = QLabel("Current Lab Code: Not Set")
        self.session_label.setStyleSheet("font-size: 24px; font-weight: bold; color: blue;")
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(self.session_label)
        
        # Connection status
        self.connection_label = QLabel("Monitor Status: Disconnected | Connected Clients: 0")
        self.connection_label.setStyleSheet("font-size: 18px; font-weight: bold; color: green;")
        self.connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(self.connection_label)
        
        # Screen sharing controls
        sharing_controls = QHBoxLayout()
        self.start_button = QPushButton("Start Sharing")
        self.stop_button = QPushButton("Stop Sharing")
        self.start_button.clicked.connect(self.start_sharing)
        self.stop_button.clicked.connect(self.stop_sharing)
        self.stop_button.setEnabled(False)
        
        sharing_controls.addWidget(self.start_button)
        sharing_controls.addWidget(self.stop_button)
        control_layout.addLayout(sharing_controls)
        
        # Performance controls
        performance_controls = QHBoxLayout()
        self.quality_label = QLabel("Quality:")
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(10)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(50)
        self.quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_value = QLabel("50%")
        self.quality_slider.valueChanged.connect(self.update_quality)
        
        performance_controls.addWidget(self.quality_label)
        performance_controls.addWidget(self.quality_slider)
        performance_controls.addWidget(self.quality_value)
        control_layout.addLayout(performance_controls)
        
        control_panel.setLayout(control_layout)
        layout.addWidget(control_panel)
        
        # Screen preview
        self.screen_label = QLabel()
        self.screen_label.setMinimumSize(800, 600)
        layout.addWidget(self.screen_label)
        
        main_widget.setLayout(layout)
        
        # Screen sharing state
        self.is_sharing = False
        self.sharing_thread = None
        self.monitor_connected = False
        self.connected_clients = 0
        self.jpeg_quality = 50
        
        # Start connection monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_connections)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def update_quality(self, value):
        self.jpeg_quality = value
        self.quality_value.setText(f"{value}%")
    
    def update_session_code(self):
        # Update the session code as user types
        self.session_code = self.code_input.text().upper()
        self.session_label.setText(f"Current Lab Code: {self.session_code}")
    
    def set_session_code(self):
        code = self.code_input.text().strip().upper()
        if len(code) != 6:
            QMessageBox.warning(self, "Error", "Code must be 6 characters long")
            return
        
        self.session_code = code
        self.session_label.setText(f"Current Lab Code: {self.session_code}")
        QMessageBox.information(self, "Success", f"Lab code set to: {self.session_code}")
    
    def monitor_connections(self):
        while True:
            try:
                # Create a temporary socket to check connections
                temp_socket = self.context.socket(zmq.SUB)
                temp_socket.setsockopt_string(zmq.SUBSCRIBE, "")
                temp_socket.connect("tcp://localhost:5555")
                
                # Try to receive data with a timeout
                temp_socket.setsockopt(zmq.RCVTIMEO, 1000)
                try:
                    temp_socket.recv()
                    self.connected_clients += 1
                except zmq.error.Again:
                    pass
                
                temp_socket.close()
                
                # Update connection status
                self.connection_label.setText(f"Monitor Status: {'Connected' if self.monitor_connected else 'Disconnected'} | Connected Clients: {self.connected_clients}")
                
                # Reset client count periodically
                time.sleep(5)
                self.connected_clients = 0
            except Exception as e:
                print(f"Error monitoring connections: {e}")
                time.sleep(5)
    
    def start_sharing(self):
        if not self.is_sharing:
            if not self.session_code:
                QMessageBox.warning(self, "Error", "Please set the lab code from the monitor first")
                return
                
            self.is_sharing = True
            self.sharing_thread = threading.Thread(target=self.share_screen)
            self.sharing_thread.daemon = True
            self.sharing_thread.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
    
    def stop_sharing(self):
        self.is_sharing = False
        if self.sharing_thread:
            self.sharing_thread.join()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def share_screen(self):
        while self.is_sharing:
            try:
                # Capture screen
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Compress and encrypt frame
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                encrypted_frame = self.cipher_suite.encrypt(buffer.tobytes())
                
                # Send frame with code
                data = {
                    'code': self.session_code,
                    'frame': encrypted_frame
                }
                self.socket.send(json.dumps(data).encode())
                
                # Update preview
                self.update_preview(frame)
                
                # Add a small delay to reduce CPU usage
                time.sleep(0.1)
            except Exception as e:
                print(f"Error sharing screen: {e}")
                break
    
    def update_preview(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.screen_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.screen_label.setPixmap(scaled_pixmap)
    
    def closeEvent(self, event):
        self.stop_sharing()
        self.socket.close()
        self.context.term()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = ServerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 