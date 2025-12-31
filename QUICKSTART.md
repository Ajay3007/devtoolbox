# QUICKSTART 🚀

Get DevToolBox running in **5 minutes** with this step-by-step guide.

## Prerequisites

- Python 3.8+
- Node.js 14.0+
- Git

## Step 1: Clone Repository (1 min)

```bash
git clone https://github.com/yourusername/devtoolbox.git
cd devtoolbox
```

## Step 2: Start Backend Server (2 min)

### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
cd backend
pip install -r requirements.txt
python app.py
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
cd backend
pip install -r requirements.txt
python app.py
```

**Expected Output**:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

✅ Backend is ready!

## Step 3: Start Frontend Server (2 min)

**Open a NEW terminal** in the project root and run:

```bash
cd frontend
npm install
npm run dev
```

**Expected Output**:
```
VITE v4.x.x  ready in xxx ms

➜  Local:   http://localhost:8080/
```

✅ Frontend is ready!

## Step 4: Open Application (Immediate)

Open your browser and go to:

### 👉 **http://localhost:8080**

You should see the DevToolBox home page with 4 tools:

1. **PCAP Editor** - Analyze and modify packet captures
2. **PCAP Generator** - Create synthetic PCAP files
3. **PCAP Merger** - Combine multiple PCAP files
4. **Hex Viewer** - Inspect binary files

---

## ⚡ Common Tasks (First Time)

### Generate a Test PCAP

1. Click **PCAP Generator** tab
2. Select **TCP** protocol
3. Set packets to **10**
4. Click **Generate PCAP**
5. Download or open in editor

### Analyze a PCAP

1. Click **PCAP Editor** tab
2. Upload a `.pcap` or `.pcapng` file (drag & drop)
3. Click any packet to see details
4. Modify fields (MAC, IP, ports, DNS, HTTP Host, TLS SNI)
5. Download modified PCAP

### Merge Multiple PCAPs

1. Click **PCAP Merger** tab
2. Select 2+ PCAP files
3. Click **Merge PCAPs**
4. Download or open merged result

### Inspect Binary File

1. Click **Hex Viewer** tab
2. Upload any binary file (`.bin`, `.dat`, firmware, etc.)
3. View as human-readable text or hex dump
4. Search for patterns
5. Export if needed

---

## 🐛 Troubleshooting

### Port Already in Use

If you see `Address already in use`, change the port:

**Backend** (edit `backend/app.py`):
```python
if __name__ == '__main__':
    app.run(port=5001)  # Changed from 5000
```

**Frontend** (edit `frontend/vite.config.js`):
```javascript
export default {
  server: { port: 8081 }  # Changed from 8080
}
```

Then restart both servers and use the new URLs.

### Module Not Found

**Backend**:
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**Frontend**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Site Can't Be Reached

1. Make sure **both servers are running** (check both terminal windows)
2. Use **http://** not https://
3. Hard refresh browser: **Ctrl+F5** (Windows) or **Cmd+Shift+R** (macOS)
4. Check Windows Firewall/antivirus isn't blocking ports 5000/8080

### Large File Uploads Fail

Edit `backend/app.py` and increase:
```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB max
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
```

---

## ✅ Verification Checklist

- [ ] Backend server running on http://localhost:5000
- [ ] Frontend server running on http://localhost:8080
- [ ] Application loads at http://localhost:8080
- [ ] Can generate test PCAP
- [ ] Can upload and view PCAP
- [ ] Can merge multiple PCAPs
- [ ] Can upload and view hex content

---

## 📚 Next Steps

- Read [RUN.md](RUN.md) for detailed running instructions
- Check [docs/](docs/) for architecture and API reference
- Try each tool with sample data
- Read [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

---

**Need help?** Open an issue on GitHub! 🎯

- Use localhost:5000/api/health to check if backend is running
- Check browser console (F12) for detailed error messages
- Use Postman to test API endpoints
- Read code comments for detailed explanations

## 🎓 Learn More

- **Vue.js Documentation:** https://vuejs.org/
- **Flask Documentation:** https://flask.palletsprojects.com/
- **Scapy Documentation:** https://scapy.readthedocs.io/
- **PCAP Format:** https://en.wikipedia.org/wiki/Pcap

## 🚀 Deploy to Production

When ready to go live:

1. **Frontend:** Push to GitHub, enable Pages in Settings
2. **Backend:** Deploy to Heroku, AWS, or DigitalOcean
3. **Update API URL:** Change axios baseURL in frontend/main.js
4. **Enable HTTPS:** Use a reverse proxy like nginx

## 📞 Get Help

- GitHub Issues: Report bugs and ask questions
- Documentation: Check docs/ folder
- Code Comments: Explore the source code

---

Happy coding! 🎉
