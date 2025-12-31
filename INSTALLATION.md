# Installation Guide 📦

Complete step-by-step installation instructions for DevToolBox on Windows, macOS, and Linux.

## System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| Python | 3.8 | 3.10+ |
| Node.js | 14.0 | 16.0+ |
| npm | 6.0 | 8.0+ |
| RAM | 2 GB | 4 GB+ |
| Disk Space | 500 MB | 1 GB |

## Prerequisites Installation

### Step 1: Install Python

**Windows**:
1. Download from https://www.python.org/downloads/
2. Run installer
3. ✅ **IMPORTANT**: Check "Add Python to PATH"
4. Click "Install Now"
5. Verify: Open PowerShell and run
```bash
python --version
```

**macOS**:
```bash
# Using Homebrew
brew install python3

# Verify
python3 --version
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# Verify
python3 --version
```

### Step 2: Install Node.js

**Windows**:
1. Download LTS from https://nodejs.org/
2. Run installer
3. Use defaults (includes npm)
4. Restart computer
5. Verify:
```bash
node --version
npm --version
```

**macOS**:
```bash
# Using Homebrew
brew install node

# Or using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 16
nvm use 16

# Verify
node --version
npm --version
```

**Linux (Ubuntu/Debian)**:
```bash
# Using apt
sudo apt-get install nodejs npm

# Or using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 16
nvm use 16

# Verify
node --version
npm --version
```

### Step 3: Install Git

**Windows**:
1. Download from https://git-scm.com/download/win
2. Run installer
3. Use defaults
4. Verify:
```bash
git --version
```

**macOS**:
```bash
brew install git
git --version
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install git
git --version
```

---

## DevToolBox Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/devtoolbox.git
cd devtoolbox
```

### Step 2: Setup Backend

#### Windows PowerShell

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# If execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Navigate to backend
cd backend

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### macOS/Linux

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Navigate to backend
cd backend

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependency Details**:
- `flask` - Web framework
- `flask-cors` - Cross-origin requests
- `scapy` - PCAP processing
- `werkzeug` - WSGI utilities

### Step 3: Setup Frontend

**All Platforms**:

```bash
# Navigate to frontend directory (from root)
cd frontend

# Install Node dependencies
npm install

# Verify packages (optional)
npm list vue axios
```

**Key Packages**:
- `vue@3` - Frontend framework
- `vite` - Build tool
- `vue-router` - Routing
- `axios` - HTTP client

---

## Verify Installation

### Backend Verification

```bash
# In backend directory with venv activated
python -c "import flask, scapy, werkzeug; print('✓ All backend dependencies installed')"
```

**Expected**: `✓ All backend dependencies installed`

### Frontend Verification

```bash
# In frontend directory
npm list vue axios vite

# Should show versions like:
# vue@3.3.x
# axios@1.6.x
# vite@4.x.x
```

### Full Application Check

```bash
# From project root
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

cd backend
python app.py
```

**Expected Output**:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

(In another terminal)

```bash
cd frontend
npm run dev
```

**Expected Output**:
```
VITE v4.x.x  ready in xxx ms

➜  Local:   http://localhost:8080/
```

---

## Troubleshooting Installation

### ❌ "python command not found"

**Windows**:
- Python not in PATH
- Solution: Reinstall Python and check "Add Python to PATH"

**macOS/Linux**:
- Use `python3` instead of `python`
```bash
python3 --version
python3 -m venv .venv
```

### ❌ "pip not found"

**Solution**:
```bash
python -m pip --version  # Use module form
python -m pip install --upgrade pip
```

### ❌ "virtual environment not created"

**Windows**:
```bash
# Try with python module
python -m venv .venv
# or
py -m venv .venv
```

**macOS/Linux**:
```bash
python3 -m venv .venv
```

### ❌ "ModuleNotFoundError after pip install"

**Solution**:
1. Verify venv is activated
2. Reinstall packages:
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### ❌ "node_modules issues"

**Solution**:
```bash
cd frontend
rm -rf node_modules
rm package-lock.json
npm cache clean --force
npm install
```

### ❌ "Scapy import error on Windows"

**Cause**: Missing WinPcap/Npcap

**Solution**:
1. Download Npcap: https://nmap.org/npcap/
2. Install with WinPcap API support enabled
3. Reinstall Scapy:
```bash
pip install --force-reinstall scapy
```

### ❌ "npm ERR! code ERESOLVE"

**Cause**: Dependency version conflicts

**Solution**:
```bash
npm install --legacy-peer-deps
# or
npm install --force
```

---

## Uninstallation

### Complete Cleanup

```bash
# Remove virtual environment
rm -rf .venv

# Remove frontend dependencies
cd frontend
rm -rf node_modules
rm package-lock.json

# Remove uploaded files
cd ../backend
rm -rf uploads/*

# Remove Python cache
rm -rf __pycache__
rm -rf .pytest_cache
```

---

## Environment Variables (Optional)

Create `backend/.env`:

```env
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_APP=app.py
MAX_FILE_SIZE=104857600
UPLOAD_FOLDER=uploads
```

Install python-dotenv:
```bash
pip install python-dotenv
```

Load in `backend/app.py`:
```python
from dotenv import load_dotenv
import os

load_dotenv()
```

---

## Next Steps

1. ✅ **Run the application** - See [RUN.md](RUN.md)
2. ✅ **Quick start** - See [QUICKSTART.md](QUICKSTART.md)
3. ✅ **Explore features** - Read [README.md](README.md)
4. ✅ **Contribute** - See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Support

If installation fails:
1. Check Python version: `python --version` (should be 3.8+)
2. Check Node version: `node --version` (should be 14+)
3. Verify all prerequisites installed
4. Try reinstalling virtual environment
5. Open GitHub issue with error message

---

**Installation complete! Ready to use DevToolBox! 🚀**