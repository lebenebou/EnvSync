
@echo off
setlocal
title Set Ethernet IP - 192.168.1.2

net session >nul 2>&1
if errorlevel 1 (
    echo Requesting administrator privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo === Ethernet IP Configuration ===
echo Detecting connected Ethernet adapter...

for /f "delims=" %%I in ('powershell -NoProfile -Command "$a = @(Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' -and $_.NdisPhysicalMedium -eq 14 }); if ($a.Count -eq 1) { $a[0].Name }"') do set "IFACE=%%I"

if not defined IFACE (
    echo ERROR: No unique connected Ethernet adapter was detected.
    echo Ensure exactly one physical Ethernet adapter is connected.
    pause
    exit /b 1
)

echo Interface  : %IFACE%
echo IP Address : 192.168.1.2
echo Subnet Mask: 255.255.255.0
echo Gateway    : 192.168.1.1
echo.
echo Applying configuration...

netsh interface ipv4 set address name="%IFACE%" source=static address=192.168.1.2 mask=255.255.255.0 gateway=192.168.1.1 gwmetric=1

if errorlevel 1 goto :error

echo.
echo Success. Press Any Key...
pause >nul
exit /b 0

:error
echo.
echo ERROR: Failed to configure the interface.
pause
exit /b 1