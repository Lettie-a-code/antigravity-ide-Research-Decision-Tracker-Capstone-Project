# 📘 Installation Instructions

## Antigravity Streamlit Project

This project is a Streamlit-based web application designed to run locally on
**Windows, macOS, or Linux**. The instructions below explain how to install
dependencies, clone the repository, and launch the application on any system.

---

## 📦 1. Requirements

Before installing, ensure you have:

- **Python 3.9+**
- **pip** (comes with Python)
- **Git** (for cloning the repository)
- **Internet connection** (first-time dependency installation)

---

## 🧰 2. Install Python

### Windows
Download Python from:
https://www.python.org/downloads/windows/

During installation:
- Check **"Add Python to PATH"**
- Choose **"Install Now"**

### macOS
Install via Homebrew:
brew install python
Or download from:
https://www.python.org/downloads/macos/

### Linux (Ubuntu/Debian)
bash
sudo apt update
sudo apt install python3 python3-pip

---

##  🔧 3. Install Git

### Windows
Download Git:
https://git-scm.com/download/win

### macOS
brew install git

### Linux
sudo apt install git

---

## 📥 4. Clone the Repository

Open a terminal (Command Prompt, PowerShell, macOS Terminal, or Linux shell):
git clone https://github.com/Lettie-a-code/antigravity-ide-Research-Decision-Tracker-Capstone-Project.git
Then enter the project folder:
cd antigravity-repo

---

## 📚 5. Install Dependencies

- Inside the project folder, run:
pip install -r requirements.txt

- If your project does not yet have a requirements.txt, you can generate one:
pip install streamlit
pip freeze > requirements.txt

---

## 🚀 6. Run the Application
From inside the project directory:
streamlit run app.py
Streamlit will open the app in your browser at: http://localhost:8501

---

## 🔄 7. Updating the App (Pulling New Changes)
If you or your teammates push updates to GitHub, pull them locally:
git pull

---

## 🛠 8. Troubleshooting
- Streamlit not found
pip install streamlit
- Permission denied (macOS/Linux)
chmod +x app.py
- Wrong Python version
Check version:
python --version






