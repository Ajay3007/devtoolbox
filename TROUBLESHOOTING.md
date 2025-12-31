# Troubleshooting Guide 🔧

Common issues, solutions, and diagnostic steps for DevToolBox.

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Backend Issues](#backend-issues)
3. [Frontend Issues](#frontend-issues)
4. [PCAP Operations](#pcap-operations)
5. [File Upload Issues](#file-upload-issues)
6. [Performance Issues](#performance-issues)
7. [Getting Help](#getting-help)

---

## Installation Issues

### ❌ Python Not Found

**Symptom**:
```
'python' is not recognized as an internal or external command
```

**Windows Solution**:
1. Reinstall Python from https://python.org
2. **CHECK** "Add Python to PATH" during installation
3. Restart command prompt
4. Verify: `python --version`

**macOS/Linux Solution**:
```bash
# Use python3 instead
python3 --version
python3 -m venv .venv
```

---

### ❌ Node.js/npm Not Found

**Symptom**:
```
'npm' is not recognized or npm: command not found
```

**Windows Solution**:
1. Download Node.js from https://nodejs.org
2. Run installer
3. Accept defaults (installs npm automatically)
4. **Restart computer**
5. Verify: `node --version` and `npm --version`

**macOS/Linux Solution**:
```bash
# Using Homebrew
brew install node

# Or using nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 16
```

---

### ❌ Virtual Environment Not Activating

**Symptom**:
```
command not found: activate or .venv\Scripts\activate not found
```

**Windows PowerShell**:
```powershell
# Allow script execution for this session
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Then activate
.venv\Scripts\Activate.ps1
```

**Windows CMD**:
```cmd
.venv\Scripts\activate.bat
```

**macOS/Linux**:
```bash
source .venv/bin/activate
```

---

### ❌ "ModuleNotFoundError: No module named 'flask'"

**Symptom**:
```
ModuleNotFoundError: No module named 'flask' or 'scapy'
```

**Solution**:
1. Verify virtual environment is activated
2. Reinstall dependencies:
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

3. Verify installation:
```bash
pip list | grep -E "flask|scapy"
```

---

## Backend Issues

### ❌ "Address Already in Use" on Port 5000

**Symptom**:
```
OSError: [Errno 48] Address already in use
or
Address already in use (Errno 98)
```

**Windows Solution**:
```powershell
# Find process on port 5000
netstat -ano | findstr :5000

# Kill it
taskkill /PID <PID_NUMBER> /F

# Or change port in backend/app.py
# Change: app.run(port=5001)
```

**macOS/Linux Solution**:
```bash
# Kill process on port 5000
kill $(lsof -t -i:5000)

# Or change port
# Edit backend/app.py: app.run(port=5001)
```

---

### ❌ Backend Runs but Frontend Can't Connect

**Symptom**:
```
Failed to fetch
CORS error: No 'Access-Control-Allow-Origin' header
Connection refused
```

**Solutions**:

1. **Verify backend is running**:
```bash
curl http://localhost:5000/api/pcap/upload
```

Should return something (not "connection refused")

2. **Check CORS is enabled in `backend/app.py`**:
```python
from flask_cors import CORS
CORS(app)
```

3. **Try different port**:
```python
if __name__ == '__main__':
    app.run(port=5001)
```

4. **Check firewall**:
- Windows Firewall might block port 5000
- macOS: System Preferences → Security & Privacy → Firewall

---

### ❌ Large File Upload Fails

**Symptom**:
```
413 Request Entity Too Large
or file upload hangs/times out
```

**Solution** in `backend/app.py`:
```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
```

Also increase Flask timeout:
```python
app.config['TIMEOUT'] = 300  # 5 minutes
```

---

### ❌ Scapy Import Error (Windows)

**Symptom**:
```
ImportError: No module named 'pcaplib'
or Scapy-related import error on Windows
```

**Solution**:
1. Install Npcap (requires WinPcap API):
   - Download: https://nmap.org/npcap/
   - **IMPORTANT**: Check "Install Npcap in WinPcap API-compatible mode"
   
2. Reinstall Scapy:
```bash
pip uninstall scapy
pip install scapy --force-reinstall
```

---

### ❌ Packet Modification Not Working

**Symptom**:
```
"Checksum calculation failed" or packet data corrupted
```

**Solution**:
1. Verify packet has required layers:
   - TCP/UDP packets need TCP/UDP layer
   - IP packets need IP layer

2. Check packet integrity:
```python
# In backend/pcap_handler.py
# Ensure _recalculate_checksums() is called after modification
```

3. Try simpler modification first:
   - Test with MAC address change (no checksum)
   - Then try IP/port changes

---

## Frontend Issues

### ❌ "npm: command not found" or npm Version Conflict

**Symptom**:
```
npm: command not found
or
ERR! code ERESOLVE, unable to resolve dependency tree
```

**Solution**:
```bash
cd frontend

# Clear npm cache
npm cache clean --force

# Remove lock file and node_modules
rm -rf node_modules package-lock.json

# Reinstall with legacy peer deps
npm install --legacy-peer-deps

# Or use npm 7+ force flag
npm install --force
```

---

### ❌ "Port 8080 Already in Use"

**Symptom**:
```
Port 8080 is already in use
```

**Solution**:

Edit `frontend/vite.config.js`:
```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 8081  // Change from 8080
  }
})
```

Then restart frontend server.

---

### ❌ Application Won't Load (Blank Screen)

**Symptom**:
- Blank white page
- No errors in console
- CORS errors

**Debugging Steps**:

1. **Check browser console** (F12 → Console tab):
   - Look for JavaScript errors
   - Check for CORS warnings

2. **Verify frontend is running**:
```
http://localhost:8080 should show loading
```

3. **Check backend is responding**:
```bash
curl http://localhost:5000/api/pcap/upload
```

4. **Hard refresh** (Ctrl+F5 or Cmd+Shift+R)

5. **Check network tab** (F12 → Network):
   - Verify requests to `/api/*` return 200 status
   - Check response content-type is application/json

---

### ❌ Hot Module Reload (HMR) Not Working

**Symptom**:
```
Changes don't reflect without manual refresh
or WebSocket connection fails
```

**Solution** in `frontend/vite.config.js`:
```javascript
export default defineConfig({
  server: {
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 8080
    }
  }
})
```

Then restart dev server.

---

### ❌ Vue Component Not Rendering

**Symptom**:
```
Component shows as [object Object]
or Route doesn't load
```

**Solution**:
1. Verify component file exists
2. Check import path in router:
```javascript
// frontend/router/index.js
import PCAPEditor from '../views/PCAPEditor.vue'
```

3. Check component is registered in routes
4. Verify no typos in route path

---

## PCAP Operations

### ❌ "Invalid PCAP File Format"

**Symptom**:
```json
{
  "success": false,
  "data": {"message": "Invalid PCAP file format"}
}
```

**Solutions**:
1. **Verify file is actual PCAP**:
```bash
# Windows
file myfile.pcap

# macOS/Linux
file myfile.pcap
```

Should show: "PCAP capture file"

2. **Try creating test PCAP**:
```bash
# If tcpdump available
tcpdump -w test.pcap -c 5 'tcp'

# Or use tcpreplay
```

3. **Upload sample PCAP**:
   - Find sample online (Wireshark sample files)
   - Try opening in Wireshark first to verify integrity

---

### ❌ Packet Modification Shows Wrong Data

**Symptom**:
- Edit MAC address but doesn't show correct value
- Modify IP but packet unchanged
- Checksum recalculation fails

**Debug Steps**:

1. **Verify packet selected**:
   - Click packet in list
   - Check details pane shows correct index

2. **Check modification endpoint**:
```bash
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{"field_path":"layers.eth.src_mac","new_value":"00:11:22:33:44:55"}' \
  http://localhost:5000/api/pcap/modify-field/uploads/test.pcap/0
```

3. **Verify modified file created**:
   - Check `backend/uploads/` folder
   - Should see `modified_*.pcap` file

---

### ❌ Generated PCAP Won't Open in Wireshark

**Symptom**:
```
Wireshark: "The file appears to be damaged or is not a PCAP file"
```

**Solution**:
1. Check file was created:
```bash
ls -la backend/uploads/
```

2. Verify file format:
```bash
file generated_pcap_filename.pcap
```

3. Try reading with Scapy directly:
```python
from scapy.all import rdpcap
packets = rdpcap('backend/uploads/filename.pcap')
print(len(packets))
```

4. If file corrupted, regenerate with simpler parameters:
   - Start with TCP protocol
   - Reduce packet count
   - Use standard IP/port

---

### ❌ Merge Creates Empty File

**Symptom**:
```
Merged PCAP has 0 packets
or merge fails silently
```

**Solution**:
1. Verify source files have packets:
```bash
# In terminal
cd backend
python
from scapy.all import rdpcap
print(len(rdpcap('uploads/file1.pcap')))
print(len(rdpcap('uploads/file2.pcap')))
```

2. Check file permissions:
   - Ensure files readable
   - Check upload folder permissions

3. Try merging simpler files first:
   - Start with generated PCAPs (known good)
   - Then try real captures

---

## File Upload Issues

### ❌ "File Size Exceeds Maximum"

**Symptom**:
```
413 Payload Too Large
or "File size exceeds maximum allowed"
```

**Solution**:

Edit `backend/app.py`:
```python
# Increase limits
MAX_FILE_SIZE = 1000 * 1024 * 1024  # 1 GB
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Also set Flask timeout
app.config['TIMEOUT'] = 600  # 10 minutes
```

---

### ❌ Upload Hangs/Times Out

**Symptom**:
```
Upload progress stops
or request timeout
```

**Solution**:
1. Check network connection
2. Try smaller file
3. Increase timeout:
```python
# backend/app.py
import signal

@app.before_request
def timeout_handler():
    signal.alarm(600)  # 10 minutes
```

4. Check browser network tab (F12):
   - See if request is still active
   - Check response headers

---

### ❌ "Unsupported File Type"

**Symptom**:
```
"Only PCAP/PCAPNG files supported" (for PCAP Editor)
or "File type not recognized" (for Hex Viewer)
```

**Solution**:

**For PCAP Editor**:
- Must be `.pcap` or `.pcapng` file
- Verify with Wireshark first
- Try converting with: `tcpdump -r oldformat.cap -w newformat.pcap`

**For Hex Viewer**:
- Supports ANY file type
- Try uploading file with correct extension
- Check file isn't corrupted

---

## Performance Issues

### ❌ Application Is Slow

**Symptom**:
- Loading takes 5+ seconds
- Scrolling packets is sluggish
- Hex viewer pagination is slow

**Solutions**:

1. **Check file size**:
   - Large PCAPs (>100MB) will be slow
   - Use PCAP Merger to split into smaller files

2. **Check system resources**:
   - Monitor CPU/RAM usage (Task Manager)
   - Close other applications

3. **Optimize backend** (`backend/app.py`):
```python
# Reduce packet details for large files
if packet_count > 10000:
    detailed = False  # Skip hex payload extraction
```

4. **Enable pagination** (frontend):
   - Already enabled for hex viewer
   - Set page size appropriately:
```javascript
const PAGE_SIZE = 5000;  // bytes per page
```

---

### ❌ Memory Usage High

**Symptom**:
- Browser using 1GB+ RAM
- Application becomes unresponsive
- "Out of memory" crashes

**Solutions**:

1. **Reduce loaded packets**:
   - Only load first 1000 packets in editor
   - Use pagination for large files

2. **Clear uploads folder**:
```bash
cd backend/uploads
rm -rf *  # Remove old files
```

3. **Restart application**:
   - Close both backend and frontend
   - Restart servers
   - Close and reopen browser tab

---

### ❌ Network Requests Slow

**Symptom**:
- API calls take 10+ seconds
- Timeouts on large file operations

**Solutions**:

1. **Check network connection**:
```bash
ping localhost
# Should show <5ms response time
```

2. **Monitor backend** (`backend/app.py`):
```python
@app.before_request
def log_request():
    import time
    request.start_time = time.time()

@app.after_request
def log_response(response):
    duration = time.time() - request.start_time
    print(f"Request took {duration:.2f}s")
    return response
```

3. **Use profiling** (optional):
```bash
pip install flask-profiler
# Add to backend/app.py per documentation
```

---

## Getting Help

### Diagnostic Information to Collect

Before asking for help, collect:

**System Info**:
```bash
# Python version
python --version

# Node version
node --version

# npm version
npm --version

# OS
# Windows: wmic os get caption
# macOS: system_profiler SPSoftwareDataType
# Linux: cat /etc/os-release
```

**Error Logs**:
1. Browser console (F12 → Console)
2. Browser network (F12 → Network)
3. Backend terminal output
4. Frontend terminal output

**File Information**:
```bash
# PCAP file info
ls -lh backend/uploads/problem_file.pcap

# Check if it's real PCAP
file backend/uploads/problem_file.pcap

# Test with Scapy
python -c "from scapy.all import rdpcap; print(len(rdpcap('backend/uploads/problem_file.pcap')))"
```

---

### Debug Mode (Backend)

Enable verbose logging:

Edit `backend/app.py`:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/api/pcap/upload', methods=['POST'])
def upload_pcap():
    logger.debug(f"Upload request received")
    logger.debug(f"File: {request.files}")
    # ... rest of function
    logger.debug(f"Processing complete")
```

---

### Debug Mode (Frontend)

Enable verbose logging:

Edit `frontend/main.js`:
```javascript
app.config.globalProperties.$debug = true;
```

In components:
```javascript
if (this.$debug) {
  console.log('Component state:', this.$data);
  console.log('API Response:', response.data);
}
```

---

### Report an Issue

When opening GitHub issue, include:

1. **Title**: Clear, specific description
   - ❌ "App doesn't work"
   - ✅ "PCAP merge fails with 'File not found' on Windows"

2. **Environment**:
   - Python version: `python --version`
   - Node version: `node --version`
   - OS: Windows 10 / macOS 12 / Ubuntu 20.04

3. **Steps to Reproduce**:
   - Exact steps to trigger issue
   - File used (if applicable)
   - Expected vs actual result

4. **Error Message**:
   - Full error text
   - Stack trace (if available)
   - Screenshots

5. **Logs**:
   - Browser console errors
   - Backend terminal output
   - Network tab responses

---

### Common Solutions Summary

| Issue | Quick Fix |
|-------|-----------|
| Port in use | `netstat -ano` then `taskkill` or change port |
| Module not found | `pip install -r requirements.txt --force-reinstall` |
| npm errors | `rm -rf node_modules` then `npm install` |
| File too large | Increase `MAX_FILE_SIZE` in `app.py` |
| Slow performance | Use pagination, split files, close other apps |
| CORS errors | Verify backend running, check `CORS(app)` |
| Blank page | Hard refresh (Ctrl+F5), check console errors |
| Can't modify packet | Try simpler edit (MAC first), check layer exists |

---

**Still having issues?** Open a GitHub issue! 🆘