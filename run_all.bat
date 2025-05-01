@echo off
start dist\server\server.exe
timeout /t 2
start dist\monitor\monitor.exe
timeout /t 2
start dist\client\client.exe
