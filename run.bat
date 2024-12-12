@echo off

:: Set the path to the PowerShell executable
set POWERSHELL_PATH=%SystemRoot%\system32\WindowsPowerShell\v1.0\powershell.exe

:: Set the path to the setup script - adjust this path as needed
set SCRIPT_PATH=%~dp0setup.ps1

:: Check if the script exists
if not exist "%SCRIPT_PATH%" (
    echo Error: setup.ps1 not found at: %SCRIPT_PATH%
    echo Please ensure the script is in the same directory as this batch file
    pause
    exit /b 1
)

:: Set the working directory to the batch file's location
cd /d "%~dp0"

:: Execute the PowerShell script with execution policy bypass
echo Executing setup script with execution policy bypass...
"%POWERSHELL_PATH%" -NoProfile -ExecutionPolicy Bypass -Command "& { Set-Location '%~dp0'; & '%SCRIPT_PATH%' }"

:: Check for errors
if %errorLevel% neq 0 (
    echo Error: Script execution failed with error level %errorLevel%
    pause
    exit /b %errorLevel%
)

echo Script execution completed successfully
pause
exit /b 0