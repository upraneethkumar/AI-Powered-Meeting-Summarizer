Step 1: # Create virtual environment

python -m venv venv

Step 2: # Activate virtual environment

venv\Scripts\activate

Step 3: # To "activate" a requirements.txt file

pip install -r requirements.txt

Step 4: To Run the application

python gui.py

Step 5: Run this in browser

http://127.0.0.1:7860




✅ How to Install Chocolatey on Windows
1️⃣ Open PowerShell as Administrator

Press Start

Type PowerShell

Right-click → Run as Administrator

2️⃣ Run This Command (Official Chocolatey Installer)

Copy & paste:
Set-ExecutionPolicy Bypass -Scope Process -Force; `
[System.Net.ServicePointManager]::SecurityProtocol = `
[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))


Re-run Chocolatey from an elevated PowerShell

Close your current PowerShell.

Open Start → PowerShell, right-click → Run as Administrator.

In the elevated PowerShell, (optional) allow running scripts for this session and activate your venv if you want choco to run while venv is active:

# allow scripts just for this session
Set-ExecutionPolicy Bypass -Scope Process -Force

# go to your project folder
cd 'D:\AI-Powered-Meeting-Summarizer'

# activate venv (optional)
& .\venv\Scripts\Activate.ps1


Install FFmpeg:

choco install ffmpeg -y


Verify:

ffmpeg -version
choco -v


If choco succeeds, you’re done.
