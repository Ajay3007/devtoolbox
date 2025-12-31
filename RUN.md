# Running DevToolBox 🚀

Complete guide for starting and managing the DevToolBox application locally.

## Prerequisites

Before running, ensure you have:
- ✅ Python 3.8+ installed
- ✅ Node.js 14+ installed
- ✅ Virtual environment created: `.venv`
- ✅ Backend dependencies installed: `pip install -r backend/requirements.txt`
- ✅ Frontend dependencies installed: `cd frontend && npm install`

## Quick Start (Standard Method)

### Terminal 1: Start Backend Server

**Windows (PowerShell)**:
```powershell
.venv\Scripts\Activate.ps1
cd backend
python app.py
```

**macOS/Linux**:
```bash
source .venv/bin/activate
cd backend
python app.py
```

**Expected Output**:
```
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

✅ Backend server running on **http://localhost:5000**

### Terminal 2: Start Frontend Server

**Windows (PowerShell)**:
```powershell
cd frontend
npm run dev
```

**macOS/Linux**:
```bash
cd frontend
npm run dev
```

**Expected Output**:
```
VITE v4.x.x  ready in xxx ms

➜  Local:   http://localhost:8080/
```

✅ Frontend server running on **http://localhost:8080**

### Step 3: Open Application

Navigate to **http://localhost:8080** in your browser 🎉

---

## Features You Can Try

### 1. PCAP Editor
- Upload existing PCAP/PCAPNG file
- View packet details
- Edit network fields (MAC, IP, ports, DNS, HTTP, TLS)
- Download modified capture

### 2. PCAP Generator
- Generate TCP flows with realistic handshakes
- Create HTTP, DNS, or TLS traffic
- Configure packet count and network settings
- Download or open in editor

### 3. PCAP Merger
- Merge 2+ PCAP files
- Preserve packet order
- Download merged result
- Open merged file in editor

### 4. Hex Viewer
- Upload any binary file
- View as text or hex dump
- Auto-detect encoding (UTF-8, ASCII, Latin-1, UTF-16, UTF-32)
- Search patterns
- Export results

---

## Alternative: Node Direct Command (Windows)

If npm scripts have PowerShell execution policy issues:

```powershell
cd frontend
node node_modules\vite\bin\vite.js
```

---

## Advanced Configuration

### Change Backend Port

Edit `backend/app.py` (around line 200):
```python
if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5001,  # Change from 5000
        debug=True
    )
```

### Change Frontend Port

Edit `frontend/vite.config.js`:
```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 8081  // Change from 8080
  }
})
```

### Increase Max Upload Size

Edit `backend/app.py`:
```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
```

### Enable CORS for Different Domains

Edit `backend/app.py`:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8080", "http://your-domain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

---

## Environment Variables

Create `backend/.env` for configuration:
```
FLASK_ENV=development
FLASK_DEBUG=True
MAX_FILE_SIZE=536870912
UPLOAD_FOLDER=uploads
```

Then load in `backend/app.py`:
```python
from dotenv import load_dotenv
import os

load_dotenv()
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_FILE_SIZE', 100*1024*1024))
```

---

## Docker Deployment

Run application in Docker container:

```bash
# Build image
docker build -t devtoolbox:latest .

# Run container
docker run -p 5000:5000 -p 8080:8080 devtoolbox:latest

# Or with volume mount for persistence
docker run -p 5000:5000 -p 8080:8080 -v $(pwd)/backend/uploads:/app/backend/uploads devtoolbox:latest
```

Access at **http://localhost:8080**

---

## Stopping Servers

### Using Keyboard Shortcut
Press **`Ctrl+C`** in each terminal window where servers are running.

### Using Task Manager (Windows)
```powershell
# Kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Kill process on port 8080
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### Using Command Line (macOS/Linux)
```bash
# Kill process on port 5000
kill $(lsof -t -i:5000)

# Kill process on port 8080
kill $(lsof -t -i:8080)
```

---

## Troubleshooting

### ❌ "Port Already in Use"

**Symptom**: `Address already in use` error on startup

**Solution**:
1. Change port in config (see "Change Backend/Frontend Port" above)
2. Or kill existing process (see "Stopping Servers" above)

### ❌ "Module Not Found" (Backend)

**Symptom**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### ❌ "npm: command not found"

**Symptom**: npm not installed or not in PATH

**Solution**:
1. Install Node.js from https://nodejs.org/
2. Verify: `node --version` and `npm --version`
3. Restart terminal after installation

### ❌ "Virtual Environment Not Activated"

**Symptom**: Module imports fail in backend

**Solution**:
```bash
# Windows
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

### ❌ "CORS Error: No 'Access-Control-Allow-Origin'"

**Symptom**: Frontend can't reach backend

**Solution**:
1. Verify backend is running: http://localhost:5000
2. Check CORS is enabled in `backend/app.py`
3. Check firewall isn't blocking port 5000

### ❌ "Site Can't Be Reached"

**Symptom**: Connection refused to http://localhost:8080

**Solution**:
1. ✅ Verify frontend server is running
2. ✅ Use correct URL: `http://` not `https://`
3. ✅ Hard refresh: **Ctrl+F5** (Windows) or **Cmd+Shift+R** (macOS)
4. ✅ Check firewall settings
5. ✅ Try different port if blocked

### ❌ "File Upload Fails" (>100MB)

**Symptom**: Upload fails for large files

**Solution**:
```python
# In backend/app.py
MAX_FILE_SIZE = 500 * 1024 * 1024  # Increase limit
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
```

### ❌ "PowerShell Execution Policy"

**Symptom**: `.venv\Scripts\Activate.ps1` blocked

**Solution**:
```powershell
# Temporary fix
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Or use batch file
.venv\Scripts\activate.bat
```

---

## Performance Tips

### Development Mode
- Vue.js will have full dev tools enabled
- Hot module reloading (HMR) active
- Flask debug mode enabled

### Production Tips
- Disable debug: Set `FLASK_ENV=production`
- Use production WSGI server (Gunicorn, uWSGI)
- Minify frontend assets: `npm run build`
- Use reverse proxy (Nginx)

---

## Next Steps

- 📖 Read [QUICKSTART.md](QUICKSTART.md) for quick examples
- 📚 Check [README.md](README.md) for feature overview
- 🔧 See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- 📋 View [docs/](docs/) for detailed documentation

---

**Happy developing!** 🎯
