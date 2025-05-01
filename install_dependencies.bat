@echo off
echo Installing Python dependencies...
pip install -r requirements.txt

echo Installing Visual C++ Redistributable...
powershell -Command "& {Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile 'vc_redist.x64.exe'}"
vc_redist.x64.exe /install /quiet /norestart
del vc_redist.x64.exe

echo Dependencies installed successfully!
pause 