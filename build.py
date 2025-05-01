import PyInstaller.__main__
import os
import shutil
import sys
import logging
import site
import subprocess
import glob

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build.log'),
        logging.StreamHandler()
    ]
)

def get_pyqt_path():
    try:
        import PyQt6
        pyqt_path = os.path.dirname(PyQt6.__file__)
        logging.info(f"Found PyQt6 at: {pyqt_path}")
        
        # Try different possible Qt6 paths
        possible_qt_paths = [
            os.path.join(pyqt_path, "Qt6"),  # Direct in PyQt6
            os.path.join(pyqt_path, "Qt"),   # Alternative path
            os.path.join(os.path.dirname(pyqt_path), "PyQt6", "Qt6"),  # Sibling directory
            os.path.join(site.getsitepackages()[0], "PyQt6", "Qt6"),   # Site packages
        ]
        
        for qt_path in possible_qt_paths:
            if os.path.exists(qt_path):
                logging.info(f"Found Qt6 at: {qt_path}")
                return qt_path
                
        # If not found in standard locations, try to find it in the Python environment
        python_path = os.path.dirname(sys.executable)
        env_qt_path = os.path.join(python_path, "Lib", "site-packages", "PyQt6", "Qt6")
        if os.path.exists(env_qt_path):
            logging.info(f"Found Qt6 in Python environment at: {env_qt_path}")
            return env_qt_path
            
        logging.error("Qt6 directory not found in any standard location")
        return None
    except ImportError:
        logging.error("PyQt6 not found!")
        return None

def get_opencv_path():
    try:
        import cv2
        cv2_path = os.path.dirname(cv2.__file__)
        logging.info(f"Found OpenCV at: {cv2_path}")
        return cv2_path
    except ImportError:
        logging.error("OpenCV not found!")
        return None

def find_dll_files(directory, pattern="*.dll"):
    """Find all DLL files in a directory and its subdirectories."""
    dll_files = []
    if not directory or not os.path.exists(directory):
        logging.warning(f"Directory not found: {directory}")
        return dll_files
        
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".dll"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory)
                dll_files.append((full_path, os.path.dirname(rel_path)))
                logging.info(f"Found DLL: {full_path}")
    return dll_files

def build_executable(name, main_file):
    print(f"\nBuilding {name} executable...")
    try:
        # Get paths for dependencies
        qt_path = get_pyqt_path()
        opencv_path = get_opencv_path()
        
        if not qt_path:
            logging.error("Could not find Qt6 directory. Please ensure PyQt6 is installed correctly.")
            return False
            
        if not opencv_path:
            logging.error("Could not find OpenCV directory. Please ensure OpenCV is installed correctly.")
            return False

        # Find all DLL files
        qt_dlls = find_dll_files(qt_path)
        opencv_dlls = find_dll_files(opencv_path)
        
        if not qt_dlls:
            logging.error(f"No DLL files found in Qt6 directory: {qt_path}")
            return False
            
        if not opencv_dlls:
            logging.error(f"No DLL files found in OpenCV directory: {opencv_path}")
            return False
        
        # Create binary tuples for PyInstaller
        binaries = []
        for dll_path, dest_dir in qt_dlls + opencv_dlls:
            if dest_dir:
                binaries.append((dll_path, dest_dir))
            else:
                binaries.append((dll_path, "."))

        # Create spec file with all necessary configurations
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{main_file}'],
    pathex=[],
    binaries={binaries},
    datas=[],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'cv2',
        'numpy',
        'zmq',
        'pyautogui',
        'PIL',
        'PIL._tkinter_finder',
        'cryptography',
        'cryptography.fernet'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{name}'
)
"""
        # Write spec file
        spec_file = f"{name}.spec"
        with open(spec_file, "w") as f:
            f.write(spec_content)
        
        # Build using spec file
        result = subprocess.run(
            ["pyinstaller", "--clean", spec_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error building {name}:")
            print(result.stderr)
            return False
            
        print(f"Successfully built {name}")
        return True
        
    except Exception as e:
        print(f"Error building {name}: {str(e)}")
        return False

def main():
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Build each component
    components = [
        ("server", "server/main.py"),
        ("client", "client/main.py"),
        ("monitor", "intermediate/main.py")
    ]
    
    success = True
    for name, main_file in components:
        if not build_executable(name, main_file):
            success = False
            print(f"\nFailed to build {name}")
            break
    
    if success:
        print("\nAll executables built successfully!")
        print("You can find them in the 'dist' directory")
        
        # Create a batch file to run all components
        with open("run_all.bat", "w") as f:
            f.write("@echo off\n")
            f.write("start dist\\server\\server.exe\n")
            f.write("timeout /t 2\n")
            f.write("start dist\\monitor\\monitor.exe\n")
            f.write("timeout /t 2\n")
            f.write("start dist\\client\\client.exe\n")
    else:
        print("\nBuild failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 