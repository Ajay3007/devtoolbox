# HTTP Host Header and TLS SNI Editing Feature

## Overview
The PCAP Editor now supports editing HTTP Host headers and TLS SNI (Server Name Indication) fields directly in captured packets. This feature automatically detects these fields and provides an intuitive interface for modification.

## Features

### 1. HTTP Host Header Editing
- **Detection**: Automatically identifies HTTP packets with Host headers
- **Extraction**: Parses and displays the current Host header value
- **Editing**: Inline editing with validation
- **Checksum Recalculation**: Automatically updates TCP/IP checksums after modification

### 2. TLS SNI Editing
- **Detection**: Identifies TLS Client Hello packets with SNI extension
- **Extraction**: Parses TLS handshake to extract SNI value
- **Editing**: Inline editing with proper TLS structure updates
- **Length Updates**: Automatically adjusts all TLS length fields (extension, handshake, record)

## How to Use

### Editing HTTP Host Header

1. **Upload a PCAP file** containing HTTP traffic
2. **Select a packet** from the packets list
3. If the packet contains an HTTP Host header, you'll see an **"HTTP Host"** field in the packet details section
4. Click the **edit icon (✏️)** next to the Host value
5. **Enter the new host** name (e.g., `www.example.com`)
6. Press **Enter** or click the **checkmark (✓)** to save
7. Press **Escape** or click the **X** to cancel

### Editing TLS SNI

1. **Upload a PCAP file** containing TLS traffic
2. **Select a packet** that is a TLS Client Hello
3. If the packet contains SNI, you'll see a **"TLS SNI"** field in the packet details section
4. Click the **edit icon (✏️)** next to the SNI value
5. **Enter the new server** name (e.g., `secure.example.com`)
6. Press **Enter** or click the **checkmark (✓)** to save
7. Press **Escape** or click the **X** to cancel

## API Endpoints

### Analyze Packet
```
GET /api/pcap/analyze/<filepath>/<packet_index>
```
**Response:**
```json
{
  "success": true,
  "data": {
    "editable": true,
    "http_host": "www.example.com",
    "tls_sni": "secure.example.com"
  }
}
```

### Modify HTTP Host
```
PUT /api/pcap/http-host/<filepath>/<packet_index>
Content-Type: application/json

{
  "host": "new-hostname.com"
}
```
**Response:**
```json
{
  "success": true,
  "data": {
    "new_host": "new-hostname.com"
  }
}
```

### Modify TLS SNI
```
PUT /api/pcap/tls-sni/<filepath>/<packet_index>
Content-Type: application/json

{
  "sni": "new-server.com"
}
```
**Response:**
```json
{
  "success": true,
  "data": {
    "new_sni": "new-server.com"
  }
}
```

## Technical Details

### HTTP Host Modification
- Uses regex pattern matching to find Host header: `Host:\s*[^\r\n]+`
- Preserves HTTP request structure
- Maintains proper line endings (CRLF)
- Updates packet length and checksums

### TLS SNI Modification
- Parses TLS record layer structure
- Navigates through TLS handshake protocol
- Locates SNI extension (type 0x0000) within extensions
- Updates multiple length fields:
  - SNI server name length
  - SNI list length
  - SNI extension data length
  - Extensions total length
  - Handshake message length
  - TLS record length
- Recalculates TCP/IP checksums

### Supported Protocols
- **HTTP**: Any HTTP/1.0 or HTTP/1.1 request with Host header
- **TLS**: TLS 1.0, 1.1, 1.2, and 1.3 Client Hello packets with SNI extension

## Limitations

1. **HTTP Host**:
   - Only works with unencrypted HTTP traffic
   - Does not support HTTP/2 or HTTP/3
   - Host header must be present in the packet

2. **TLS SNI**:
   - Only works with Client Hello packets
   - SNI extension must be present
   - Cannot modify encrypted SNI (ESNI)
   - New SNI length must fit within packet MTU

3. **General**:
   - Modified packets must be within MTU limits
   - Fragmented packets may require special handling
   - Checksum offloading may affect packet validation

## Error Handling

The system provides detailed error messages:
- `"Invalid packet index"` - Packet number out of range
- `"Not an HTTP packet"` - Selected packet is not HTTP
- `"No Host header found"` - HTTP packet lacks Host header
- `"Not a TLS Client Hello packet"` - Not a TLS handshake
- `"No SNI extension found"` - TLS packet lacks SNI
- `"Invalid TLS structure"` - Malformed TLS packet

## Use Cases

### Security Testing
- Test web application behavior with different Host headers
- Verify server SNI handling
- Simulate virtual host routing

### Traffic Analysis
- Modify packet captures for replay testing
- Create test scenarios with specific hostnames
- Anonymize traffic logs by changing hostnames

### Development & Debugging
- Test load balancer configurations
- Verify reverse proxy setups
- Debug SSL/TLS certificate selection

## Best Practices

1. **Backup Original PCAP**: Always keep a copy of the original file
2. **Verify Changes**: Check modified packets before using them
3. **Test Incrementally**: Modify one packet at a time for testing
4. **Download Modified File**: Use the "Download Modified PCAP" button to save changes
5. **Validate Traffic**: Use tools like Wireshark to verify modified packets

## Example Workflow

```plaintext
1. Upload capture.pcap
2. Navigate to packet #42 (HTTP GET request)
3. See "HTTP Host: api.example.com"
4. Click edit icon
5. Change to "api-staging.example.com"
6. Save changes
7. Download modified PCAP
8. Replay modified traffic for testing
```

## Future Enhancements

Potential future additions:
- Batch editing multiple packets
- HTTP/2 :authority pseudo-header support
- ESNI (Encrypted SNI) handling
- Custom header injection
- SNI wildcard support
- Import/export host mappings
