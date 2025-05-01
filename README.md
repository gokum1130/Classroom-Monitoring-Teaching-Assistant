# Classroom Monitoring System

A secure, real-time classroom monitoring system that allows instructors to view student screens while maintaining privacy and security through lab codes.

## Overview

This system consists of three main components:

1. **Server Application**: The central hub that manages connections and screen sharing.
2. **Monitor Application**: Used by instructors to view student screens and manage lab codes.
3. **Client Application**: Used by students to connect to the monitoring system and share their screens.

## Features

- **Secure Connection**: Students must enter a valid lab code to connect
- **Real-time Screen Sharing**: Low-latency screen sharing with adjustable quality
- **Multiple Client Support**: Handles 30+ simultaneous client connections
- **Connection Monitoring**: Real-time status updates for all connections
- **Reconnection Logic**: Automatic reconnection attempts if connection is lost
- **Encrypted Communication**: All data is encrypted for security

## Installation

### Prerequisites

- Python 3.8 or higher
- PyQt6
- OpenCV
- PyZMQ
- PyAutoGUI
- Pillow
- Cryptography

### Setup

1. Clone the repository:
```
git clone https://github.com/yourusername/classroom-monitoring.git
cd classroom-monitoring
```

2. Create and activate a virtual environment:
```
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Build the executables:
```
python build.py
```

## Usage

### Starting the Applications

1. Start the Server:
```
dist\server\server.exe
```

2. Start the Monitor (instructor):
```
dist\monitor\monitor.exe
```

3. Start the Client (student):
```
dist\client\client.exe
```

Alternatively, use the provided batch file to start all components:
```
run_all.bat
```

### Monitor Application

1. Launch the Monitor application
2. The current lab code will be displayed
3. You can:
   - Enter a new 6-character code
   - Generate a random code
   - Refresh client connections
4. Student screens will appear in the grid layout

### Client Application

1. Launch the Client application
2. Enter:
   - Username
   - Password
   - Lab Code (must match Monitor's code)
   - Monitor IP Address (default: localhost)
3. Click Login
4. Your screen will be shared with the Monitor

## Security Features

- **Lab Code Verification**: Students must enter the exact code displayed on the Monitor
- **Encrypted Communication**: All screen data is encrypted
- **Connection Validation**: Regular verification of client connections
- **Secure Disconnection**: Proper cleanup of resources on disconnect

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify the Monitor IP address is correct
   - Check if the Server is running
   - Ensure the lab code matches exactly

2. **Screen Not Sharing**
   - Verify the lab code is correct
   - Check your internet connection
   - Restart the Client application

3. **Monitor Not Receiving Screens**
   - Verify the Server is running
   - Check the lab code
   - Ensure clients are properly connected

### Logs

- Check the application logs in the `logs` directory
- Monitor the connection status in the applications
- Review error messages in the console

## Development

### Project Structure

```
classroom-monitoring/
├── server/
│   └── main.py
├── intermediate/
│   └── main.py
├── client/
│   └── main.py
├── build.py
├── requirements.txt
└── README.md
```

### Building from Source

1. Modify the source code as needed
2. Run the build script:
```
python build.py
```
3. The executables will be created in the `dist` directory

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- Your Name - Initial work

## Acknowledgments

- PyQt6 for the GUI framework
- OpenCV for image processing
- ZMQ for network communication 