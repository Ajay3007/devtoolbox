# DevToolBox - AI Agent Instructions

## Project Architecture

**Hybrid Web App**: Flask backend + Vue.js 3 frontend for network packet analysis tools

- **Backend** ([backend/](backend/)): Python/Flask REST API using Scapy for PCAP manipulation
- **Frontend** ([frontend/](frontend/)): Vue 3 + Vite with Vue Router for SPA
- **Docs** ([docs/](docs/)): Static HTML documentation for GitHub Pages

## Critical Modified File Pattern

**PCAP modifications create copies**: When editing packets, the system automatically creates `modified_<filename>.pcap` in `backend/uploads/` to preserve originals. See `PCAPHandler._get_modified_filepath()` in [backend/pcap_handler.py](backend/pcap_handler.py#L17-L32).

## Key Development Workflows

### Running the Application

```powershell
# Terminal 1: Backend (from project root)
cd backend
..\\.venv\Scripts\Activate.ps1  # Uses project-level venv
python app.py  # Runs on localhost:5000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev  # Runs on localhost:8080
```

### PCAP Packet Editing

All packet modifications follow this pattern in [backend/pcap_handler.py](backend/pcap_handler.py):
1. Read packets with `rdpcap(filepath)`
2. Modify packet layers (IP/TCP/UDP/Raw)
3. Call `_recalculate_checksums()` to delete and auto-rebuild checksums
4. Write with `wrpcap(filepath, packets)`

**Example**: HTTP Host header editing uses regex replacement in Raw layer then triggers checksum recalc (see `modify_http_host()` at [pcap_handler.py#L287](backend/pcap_handler.py#L287)).

## Special Features

### HTTP Host & TLS SNI Editing

**Two specialized endpoints** for protocol-aware editing:
- `PUT /api/pcap/http-host/<filepath>/<index>` - Regex-based Host header replacement
- `PUT /api/pcap/tls-sni/<filepath>/<index>` - Binary TLS structure parsing and SNI modification

TLS SNI editing involves:
1. Parse TLS record → handshake → extensions structure
2. Locate SNI extension (type 0x0000) via binary traversal
3. Replace SNI string and update all length fields (extension, handshake, record)
4. See `_replace_sni_in_payload()` for binary manipulation logic at [pcap_handler.py#L438](backend/pcap_handler.py#L438)

### Frontend Editable Fields

[frontend/views/PCAPEditor.vue](frontend/views/PCAPEditor.vue) provides inline editing for:
- MAC addresses (src/dst)
- VLAN IDs
- IPv4/IPv6 addresses and ports
- DNS query names and response IPs
- HTTP Host headers
- TLS SNI

Each uses Vue reactive bindings with edit/save/cancel pattern. Always call backend API for actual modification.

## API Response Convention

All endpoints use standardized format from [backend/utils.py](backend/utils.py):
```python
{
  "success": bool,
  "status_code": int,
  "data": dict | {"message": str}
}
```

## Common Patterns

**File Upload**: Uses `secure_filename()` + timestamp prefix (`YYYYMMDD_HHMMSS_`) for uniqueness in [backend/app.py](backend/app.py#L62-L64)

**Packet Analysis**: Extract detailed info in `_extract_packet_info()` with `detailed=True` flag to include hex payloads at [pcap_handler.py#L188](backend/pcap_handler.py#L188)

**Error Handling**: Backend returns standardized error responses; frontend displays inline error messages (no global error modal)

## Dependencies

**Backend**: Flask, flask-cors, scapy (see [backend/requirements.txt](backend/requirements.txt))
**Frontend**: Vue 3, Vue Router, Axios (see [frontend/package.json](frontend/package.json))

## Testing Approach

No formal test suite exists. Manual testing workflow:
1. Generate test PCAPs with `tcpdump -w test.pcap`
2. Upload via frontend or `curl -F "file=@test.pcap" http://localhost:5000/api/pcap/upload`
3. Verify modifications with Wireshark

## Environment Notes

- **Windows development**: Uses PowerShell, path format `c:\Users\...`
- **Virtual environment**: `.venv` at project root (not in backend/)
- **Port conflicts**: Change ports in [backend/app.py](backend/app.py) (`app.run(port=)`) and [frontend/vite.config.js](frontend/vite.config.js)
