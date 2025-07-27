@echo off
REM Create a virtual environment named 'venv'
python -m venv venv

REM Activate the virtual environment
call venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
pip install -r requirements.txt

echo Environment setup complete.