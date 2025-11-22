# PowerShell script to run create_message_feedback_table.py with venv
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Activate venv if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
}

python scripts\create_message_feedback_table.py

