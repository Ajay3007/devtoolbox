# API Reference 🔌

Complete REST API documentation for DevToolBox backend services.

## Base URL

```
http://localhost:5000/api
```

## Response Format

All endpoints return standardized JSON responses:

```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "key": "value"
  }
}
```

**Error Response**:
```json
{
  "success": false,
  "status_code": 400,
  "data": {
    "message": "Error description"
  }
}
```

## Authentication

No authentication required for local development. Production deployments should implement:
- API key validation
- JWT tokens
- OAuth2 (for public APIs)

---

## PCAP Endpoints

### Upload PCAP File

**Endpoint**: `POST /pcap/upload`

**Description**: Upload and parse a PCAP/PCAPNG file

**Request**:
```
Content-Type: multipart/form-data

Parameters:
- file (binary, required): PCAP or PCAPNG file
```

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "filename": "20251229_105402_ipv4Get1pkt.pcap",
    "filepath": "uploads/20251229_105402_ipv4Get1pkt.pcap",
    "size": 65540,
    "packet_count": 1,
    "packets": [
      {
        "index": 0,
        "size": 54,
        "timestamp": 1234567890.123,
        "packet_type": "SYN",
        "layers": {
          "eth": {"src_mac": "00:11:22:33:44:55", "dst_mac": "aa:bb:cc:dd:ee:ff"},
          "ip": {"src": "192.168.1.1", "dst": "192.168.1.2", "version": 4},
          "tcp": {"src_port": 1234, "dst_port": 80, "flags": "S"}
        }
      }
    ]
  }
}
```

**Status Codes**:
- `200` - Success
- `400` - Invalid file format
- `413` - File too large
- `500` - Server error

---

### Get PCAP File

**Endpoint**: `GET /pcap/file/<filepath>`

**Description**: Retrieve and parse existing PCAP file

**Parameters**:
- `filepath` (string, URL path): File path relative to uploads folder

**Response**: Same as Upload response

**Example**:
```
GET /api/pcap/file/uploads/myfile.pcap
GET /api/pcap/file/20251229_105402_ipv4Get1pkt.pcap
```

---

### Generate PCAP File

**Endpoint**: `POST /pcap/generate`

**Description**: Generate synthetic PCAP with specified protocol and parameters

**Request**:
```json
{
  "protocol": "TCP",
  "packet_count": 10,
  "src_mac": "00:11:22:33:44:55",
  "dst_mac": "aa:bb:cc:dd:ee:ff",
  "src_ip": "192.168.1.1",
  "dst_ip": "192.168.1.2",
  "src_port": 1234,
  "dst_port": 80,
  "vlan_id": null,
  "options": {
    "http_host": "example.com",
    "dns_query": "google.com",
    "tls_sni": "example.com"
  }
}
```

**Supported Protocols**:
- `TCP` - Pure TCP flows
- `HTTP` - HTTP over TCP
- `UDP` - UDP datagrams
- `DNS_UDP` - DNS over UDP
- `DNS_TCP` - DNS over TCP
- `TLS` - TLS/SSL handshake

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "filename": "20251229_143404_test.pcap",
    "filepath": "uploads/20251229_143404_test.pcap",
    "size": 524,
    "packet_count": 10,
    "packets": [...]
  }
}
```

---

### Merge PCAP Files

**Endpoint**: `POST /pcap/merge`

**Description**: Merge 2 or more PCAP files into single capture

**Request**:
```
Content-Type: multipart/form-data

Parameters:
- files[] (binary array, required): 2+ PCAP files
- output_name (string, optional): Custom output filename (no extension)
```

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "filename": "merged_20251229_143500.pcap",
    "filepath": "uploads/merged_20251229_143500.pcap",
    "size": 1048,
    "packet_count": 50,
    "source_files": [
      {"filename": "file1.pcap", "packet_count": 25},
      {"filename": "file2.pcap", "packet_count": 25}
    ]
  }
}
```

---

### Export PCAP File

**Endpoint**: `GET /pcap/export/<filepath>`

**Description**: Download PCAP file as binary

**Parameters**:
- `filepath` (string, URL path): File path to export

**Response**: Binary PCAP file

**Example**:
```
GET /api/pcap/export/uploads/myfile.pcap
```

---

### Modify HTTP Host

**Endpoint**: `PUT /pcap/http-host/<filepath>/<packet_index>`

**Description**: Modify HTTP Host header in packet

**Request**:
```json
{
  "old_host": "example.com",
  "new_host": "newexample.com"
}
```

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "message": "HTTP Host modified successfully",
    "modified_file": "uploads/modified_20251229_121937_http_ipv6_host_contain_domain.pcap"
  }
}
```

---

### Modify TLS SNI

**Endpoint**: `PUT /pcap/tls-sni/<filepath>/<packet_index>`

**Description**: Modify TLS Server Name Indication (SNI)

**Request**:
```json
{
  "old_sni": "example.com",
  "new_sni": "newexample.com"
}
```

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "message": "TLS SNI modified successfully",
    "modified_file": "uploads/modified_20251229_135122_tls_ipv4_sni_contain_domain.pcap"
  }
}
```

---

### Modify Packet Field

**Endpoint**: `PUT /pcap/modify-field/<filepath>/<packet_index>`

**Description**: Generic packet field modification

**Request**:
```json
{
  "field_path": "layers.eth.src_mac",
  "new_value": "00:11:22:33:44:55"
}
```

**Supported Fields**:
- `layers.eth.src_mac` - Source MAC address
- `layers.eth.dst_mac` - Destination MAC address
- `layers.ip.src` - Source IP
- `layers.ip.dst` - Destination IP
- `layers.tcp.src_port` - TCP source port
- `layers.tcp.dst_port` - TCP destination port
- `layers.udp.src_port` - UDP source port
- `layers.udp.dst_port` - UDP destination port
- `layers.vlan.id` - VLAN ID
- `layers.dns.query_name` - DNS query name
- `layers.http.host` - HTTP Host header

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "message": "Packet field modified",
    "modified_file": "uploads/modified_<original_filename>.pcap"
  }
}
```

---

## Hex Viewer Endpoints

### Upload File for Hex Viewing

**Endpoint**: `POST /hex/upload`

**Description**: Upload binary file and get hex representation with encoding detection

**Request**:
```
Content-Type: multipart/form-data

Parameters:
- file (binary, required): Any binary file
```

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "filename": "firmware.bin",
    "filepath": "uploads/firmware.bin",
    "size": 1024,
    "file_type": "binary",
    "encoding": "utf-8",
    "hex": "89504e470d0a1a0a0000000d...",
    "text": "PNG image data...",
    "is_readable": false
  }
}
```

**File Type Detection**:
- `json` - JSON document
- `xml` - XML document
- `text` - Plain text
- `binary` - Binary file

**Encoding Detection**:
- `utf-8` - UTF-8 unicode
- `ascii` - 7-bit ASCII
- `latin-1` - ISO-8859-1
- `utf-16` - UTF-16 unicode
- `utf-32` - UTF-32 unicode

---

### Get Hex File

**Endpoint**: `GET /hex/file/<filepath>`

**Description**: Retrieve hex representation of uploaded file

**Parameters**:
- `filepath` (string, URL path): File path

**Query Parameters**:
- `offset` (int, optional): Byte offset to start from
- `length` (int, optional): Number of bytes to retrieve
- `page` (int, optional): Page number for pagination (default: 1)
- `page_size` (int, optional): Bytes per page (default: 1024)

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "hex_data": "89504e470d0a1a0a0000000d49484452...",
    "text_data": "PNG image\r\n...",
    "file_type": "binary",
    "encoding": "utf-8",
    "offset": 0,
    "length": 1024,
    "total_size": 2048,
    "page": 1,
    "total_pages": 2
  }
}
```

---

## Error Handling

### Common Error Responses

**Invalid File Format**:
```json
{
  "success": false,
  "status_code": 400,
  "data": {
    "message": "Invalid PCAP file format"
  }
}
```

**File Not Found**:
```json
{
  "success": false,
  "status_code": 404,
  "data": {
    "message": "File not found"
  }
}
```

**File Too Large**:
```json
{
  "success": false,
  "status_code": 413,
  "data": {
    "message": "File size exceeds maximum allowed (100 MB)"
  }
}
```

**Server Error**:
```json
{
  "success": false,
  "status_code": 500,
  "data": {
    "message": "Internal server error"
  }
}
```

---

## Rate Limiting

Current limits (production should implement):
- Upload: 100 files/hour per IP
- Generate: 1000 packets/hour per IP
- Merge: 50 merges/hour per IP

---

## CORS Support

All endpoints support Cross-Origin Resource Sharing (CORS):

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

---

## Example Requests

### Using cURL

**Upload PCAP**:
```bash
curl -X POST \
  -F "file=@myfile.pcap" \
  http://localhost:5000/api/pcap/upload
```

**Generate PCAP**:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "protocol": "HTTP",
    "packet_count": 5,
    "src_ip": "192.168.1.1",
    "dst_ip": "192.168.1.2",
    "options": {"http_host": "example.com"}
  }' \
  http://localhost:5000/api/pcap/generate
```

**Merge PCAPs**:
```bash
curl -X POST \
  -F "files=@file1.pcap" \
  -F "files=@file2.pcap" \
  -F "output_name=combined" \
  http://localhost:5000/api/pcap/merge
```

### Using Axios (JavaScript)

**Upload**:
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

axios.post('http://localhost:5000/api/pcap/upload', formData)
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

**Generate**:
```javascript
axios.post('http://localhost:5000/api/pcap/generate', {
  protocol: 'TCP',
  packet_count: 10,
  src_ip: '192.168.1.1',
  dst_ip: '192.168.1.2'
})
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

---

## Webhooks (Future)

Planned webhook support for automation:
- `packet.modified` - Triggered when packet is edited
- `file.merged` - Triggered when files are merged
- `file.generated` - Triggered when PCAP is generated

---

## Rate Limiting Headers

Response includes rate limit info:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

---

## Versioning

Current API Version: `v1`

Future changes will support version negotiation:
```
Accept: application/vnd.devtoolbox.v2+json
```

---

## Support & Issues

For API questions or bugs:
1. Check this documentation
2. Review [FEATURES.md](FEATURES.md) for capabilities
3. Open GitHub issue with:
   - Endpoint used
   - Request payload
   - Error response
   - Steps to reproduce

---

**Happy coding! 🚀**