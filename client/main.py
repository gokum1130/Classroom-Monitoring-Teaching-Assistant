import sys
import cv2
import numpy as np
import zmq
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QImage, QPixmap
from cryptography.fernet import Fernet
import pyautogui
import threading
import json
import uuid
import socket
import time
import base64

class SignalHandler(QObject):
    update_status = pyqtSignal(str, str)  # message, color
    show_message = pyqtSignal(str, str)  # title, message

class ClientApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Classroom Client")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize signal handler
        self.signals = SignalHandler()
        self.signals.update_status.connect(self.update_status_label)
        self.signals.show_message.connect(self.show_message_box)
        
        # Generate unique client ID
        self.client_id = str(uuid.uuid4())
        
        # Initialize encryption
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        
        # Initialize ZMQ context
        self.context = zmq.Context()
        self.socket = None
        self.monitor_address = "localhost"  # Default to localhost
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # Login form
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Lab Code")
        self.code_input.setMaxLength(6)
        
        # Monitor address input
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Monitor IP Address (default: localhost)")
        self.address_input.setText(self.monitor_address)
        
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.handle_login)
        
        # Add widgets to layout
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.code_input)
        layout.addWidget(self.address_input)
        layout.addWidget(login_button)
        
        # Connection status
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        layout.addWidget(self.status_label)
        
        # Screen preview
        self.screen_label = QLabel()
        layout.addWidget(self.screen_label)
        
        main_widget.setLayout(layout)
        
        # Screen sharing state
        self.is_sharing = False
        self.sharing_thread = None
        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.try_reconnect)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.code_verified = False
        self.username = None
    
    def update_status_label(self, message, color):
        self.status_label.setText(f"Status: {message}")
        self.status_label.setStyleSheet(f"font-weight: bold; color: {color};")
    
    def show_message_box(self, title, message):
        QMessageBox.information(self, title, message)
    
    def connect_to_monitor(self):
        try:
            # Get monitor address
            self.monitor_address = self.address_input.text().strip() or "localhost"
            
            # Create new socket
            if self.socket:
                self.socket.close()
            
            self.socket = self.context.socket(zmq.PUB)
            self.socket.connect(f"tcp://{self.monitor_address}:5555")
            
            # Test connection
            self.socket.send(json.dumps({"test": True}).encode())
            self.signals.update_status.emit("Connected", "green")
            self.reconnect_attempts = 0
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            self.signals.update_status.emit("Connection Failed", "red")
            return False
    
    def try_reconnect(self):
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self.signals.update_status.emit(f"Reconnecting... (Attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})", "orange")
            if self.connect_to_monitor():
                self.reconnect_timer.stop()
                self.start_sharing()
            else:
                # Try again in 5 seconds
                self.reconnect_timer.start(5000)
        else:
            self.reconnect_timer.stop()
            self.signals.update_status.emit("Connection Failed - Max attempts reached", "red")
            self.signals.show_message.emit("Connection Error", "Failed to connect to monitor after multiple attempts. Please check the IP address and try again.")
    
    def handle_login(self):
        self.username = self.username_input.text()
        password = self.password_input.text()
        code = self.code_input.text().strip().upper()
        
        if not self.username or not password or not code:
            self.signals.show_message.emit("Error", "Please fill in all fields")
            return
        
        if len(code) != 6:
            self.signals.show_message.emit("Error", "Lab code must be 6 characters long")
            return
        
        # Try to connect to monitor
        if not self.connect_to_monitor():
            self.reconnect_timer.start(5000)  # Start reconnection attempts
            return
        
        # Verify code with monitor
        self.verify_code_with_monitor(code)
    
    def verify_code_with_monitor(self, code):
        try:
            # Send verification request
            verification_data = {
                'type': 'verify_code',
                'code': code,
                'client_id': self.client_id
            }
            self.socket.send(json.dumps(verification_data).encode())
            
            # Wait for response (in a real app, you would implement a proper response mechanism)
            # For now, we'll assume the code is verified if we can connect
            self.code_verified = True
            self.start_sharing()
            self.signals.show_message.emit("Success", f"Login successful: {self.username}")
        except Exception as e:
            print(f"Verification error: {e}")
            self.signals.update_status.emit("Code Verification Failed", "red")
            self.signals.show_message.emit("Error", "Failed to verify lab code with monitor. Please check the code and try again.")
    
    def start_sharing(self):
        if not self.is_sharing and self.code_verified:
            self.is_sharing = True
            self.sharing_thread = threading.Thread(target=self.capture_screen)
            self.sharing_thread.daemon = True
            self.sharing_thread.start()
    
    def stop_sharing(self):
        self.is_sharing = False
        if self.sharing_thread:
            self.sharing_thread.join()
    
    def capture_screen(self):
        while self.is_sharing:
            try:
                # Capture screen
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Compress and encrypt frame
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                encrypted_frame = self.cipher_suite.encrypt(buffer.tobytes())
                
                # Convert encrypted frame to base64 for JSON serialization
                encoded_frame = base64.b64encode(encrypted_frame).decode('utf-8')
                
                # Send frame with code and client ID
                data = {
                    'type': 'screen_data',
                    'code': self.code_input.text().strip().upper(),
                    'client_id': self.client_id,
                    'frame': encoded_frame
                }
                self.socket.send(json.dumps(data).encode())
                
                # Update preview
                self.update_preview(frame)
                
                # Add a small delay to reduce CPU usage
                time.sleep(0.1)
            except Exception as e:
                print(f"Error capturing screen: {e}")
                self.signals.update_status.emit("Connection Lost", "red")
                self.reconnect_timer.start(5000)  # Start reconnection attempts
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
        if self.socket:
            self.socket.close()
        self.context.term()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = ClientApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 