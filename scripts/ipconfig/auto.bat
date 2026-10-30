
@echo off
setlocal
title Set Ethernet IP - Automatic DHCP

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
echo IP Address : Automatic (DHCP)
echo DNS Servers: Automatic (DHCP)
echo.
echo Applying configuration...

netsh interface ipv4 set address name="%IFACE%" source=dhcp
if errorlevel 1 goto :error

netsh interface ipv4 set dnsservers name="%IFACE%" source=dhcp
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