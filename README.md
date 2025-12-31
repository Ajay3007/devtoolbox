# DevToolBox 🛠️

A comprehensive suite of developer tools for data plane analysis, network packet manipulation, and binary file inspection. Built with Flask + Vue.js 3.

## 🎯 Overview

DevToolBox is a hybrid web-based application featuring **4 powerful utilities**:

| Tool | Purpose | Use Case |
|------|---------|----------|
| **PCAP Editor** | Read, analyze, and modify network packet captures | Packet forensics, protocol testing, traffic analysis |
| **PCAP Generator** | Generate synthetic PCAP files with complete TCP flows | Test data creation, simulation, stress testing |
| **PCAP Merger** | Combine multiple PCAP files into one | Consolidate captures, merge test data |
| **Hex Viewer** | View and search binary files in hex/text formats | Firmware analysis, file forensics, protocol debugging |

## ✨ Key Features

### PCAP Editor
- Upload and analyze PCAP/PCAPNG files
- View detailed packet information with protocol breakdown
- Modify packet types (detect SYN, SYN-ACK, FIN, RST, ACK, PSH-ACK, UDP, ICMP)
- Edit network fields: MAC addresses, IP addresses, ports, VLAN IDs
- Modify HTTP Host headers and TLS SNI fields
- Edit DNS queries with live packet updates
- Automatic checksum recalculation
- Download modified captures
- File statistics and packet counting

### PCAP Generator
- Generate synthetic packets with complete TCP 3-way handshake flows
- Support multiple protocols: TCP, HTTP, UDP, DNS (UDP/TCP), TLS
- Incremental destination IP addresses for unique flows
- VLAN tagging support
- Custom network configurations (MAC, IP, ports)
- Full TCP lifecycle: SYN → SYN-ACK → ACK → Data → FIN-ACK
- Protocol-specific payloads (HTTP requests/responses, DNS queries, TLS Client Hello)

### PCAP Merger
- Merge 2+ PCAP/PCAPNG files into single capture
- Preserve packet order and timing
- Custom output filename
- Automatic packet counting

### Hex Viewer
- Upload any binary file
- Dual view mode: Human-readable text + Hex dump
- Auto-detect encoding (UTF-8, ASCII, Latin-1, UTF-16, UTF-32)
- Format detection (JSON, XML, Plain Text, Binary)
- Search by hex pattern or ASCII text
- Pagination for large files
- Export capabilities (hex dump, text content)
- Copy to clipboard

## 🏗️ Project Structure

```
devtoolbox/
├── backend/
│   ├── app.py                  # Flask API server
│   ├── pcap_handler.py         # PCAP processing logic
│   ├── utils.py                # Utility functions
│   ├── requirements.txt         # Python dependencies
│   └── uploads/                # File storage
├── frontend/
│   ├── views/
│   │   ├── Home.vue            # Landing page
│   │   ├── PCAPEditor.vue      # Editor tool
│   │   ├── PCAPGenerator.vue   # Generator tool
│   │   ├── PCAPMerger.vue      # Merger tool
│   │   └── HexViewer.vue       # Hex viewer tool
│   ├── router/
│   │   └── index.js            # Route definitions
│   ├── App.vue                 # Root component
│   ├── main.js                 # Entry point
│   ├── vite.config.js          # Vite configuration
│   ├── package.json            # Node dependencies
│   └── index.html              # HTML template
├── docs/                       # GitHub Pages documentation
├── .github/
│   └── copilot-instructions.md # AI agent guide
├── README.md                   # This file
├── QUICKSTART.md               # 5-minute setup
├── RUN.md                      # Running instructions
├── LICENSE                     # MIT License
└── .gitignore                  # Git ignore rules
```

## 🛠️ Tech Stack

**Backend**: Python 3.8+ with Flask, Scapy  
**Frontend**: Vue.js 3, Vite, Axios  
**PCAP Processing**: Scapy library  
**Deployment**: Docker-ready (Dockerfile included)

## 📋 Requirements

- **Python**: 3.8 or higher
- **Node.js**: 14.0 or higher  
- **npm**: 6.0 or higher
- **Git**: for version control

## 🚀 Quick Start (5 Minutes)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/devtoolbox.git
cd devtoolbox
```

### 2. Setup Backend (Terminal 1)
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

cd backend
pip install -r requirements.txt
python app.py
```
✅ Backend running at **http://localhost:5000**

### 3. Setup Frontend (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```
✅ Frontend running at **http://localhost:8080**

### 4. Open in Browser
Navigate to **http://localhost:8080** 🎉

## 📚 Usage Guide

### PCAP Editor
1. Navigate to **PCAP Editor** tab
2. Upload a PCAP/PCAPNG file (drag & drop or click)
3. View packets in the list
4. Click packet to see details
5. Modify network fields (MACs, IPs, ports, DNS, HTTP Host, TLS SNI)
6. Download modified PCAP

### PCAP Generator
1. Go to **PCAP Generator** tab
2. Select protocol (TCP, HTTP, UDP, DNS, TLS)
3. Configure packet count and network settings
4. Click "Generate PCAP"
5. Open in Editor or Download

### PCAP Merger
1. Navigate to **PCAP Merger** tab
2. Select 2+ PCAP files
3. Optionally set output filename
4. Click "Merge PCAPs"
5. View merged result and download

### Hex Viewer
1. Go to **Hex Viewer** tab
2. Upload any binary file
3. View automatically detected format (text/JSON/XML/binary)
4. Toggle between Text View and Hex View
5. Search for patterns
6. Export as needed

## 🐳 Docker Deployment

```bash
# Build image
docker build -t devtoolbox .

# Run container
docker run -p 5000:5000 -p 8080:8080 devtoolbox
```

## 🔧 Troubleshooting

### Port Already in Use
**Frontend** (change in `frontend/vite.config.js`):
```javascript
export default {
  server: { port: 8081 }
}
```

**Backend** (change in `backend/app.py`):
```python
if __name__ == '__main__':
    app.run(port=5001)
```

### Module Not Found
```bash
# Backend
cd backend
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Site Can't Be Reached
- Verify both servers are running
- Use correct URLs: http://localhost:8080 (not https)
- Hard refresh: Ctrl+F5 (or Cmd+Shift+R on macOS)
- Check firewall/antivirus settings

### Large File Upload Issues
Edit `backend/app.py`:
```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # Increase as needed
```

## 📖 Documentation

- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide
- [RUN.md](RUN.md) - Detailed running instructions
- [API Reference](docs/api-reference.html) - REST API endpoints
- [Architecture](docs/architecture.html) - System design
- [Contributing](CONTRIBUTING.md) - Contribution guidelines

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

Built for data plane developers and software engineers who need efficient tools for packet analysis and binary file inspection.

## 🙋 Support

For issues, questions, or feature requests, please [open an issue](https://github.com/yourusername/devtoolbox/issues) on GitHub.

---

**Happy analyzing!** 🚀
