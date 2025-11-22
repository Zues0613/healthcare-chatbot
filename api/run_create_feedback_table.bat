@echo off
REM Batch script to run create_message_feedback_table.py with venv
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python scripts\create_message_feedback_table.py
pause

