# Features Guide 🎯

Detailed documentation of all DevToolBox features and capabilities.

## Table of Contents
1. [PCAP Editor](#pcap-editor)
2. [PCAP Generator](#pcap-generator)
3. [PCAP Merger](#pcap-merger)
4. [Hex Viewer](#hex-viewer)

---

## PCAP Editor 📊

### Overview
Professional-grade PCAP file analyzer and editor with inline packet modification capabilities.

### Key Features

#### Upload & Analysis
- **Drag-and-drop** PCAP/PCAPNG file upload
- **Auto-parsing** with packet count display
- **Progress tracking** during upload
- **File statistics**: Total size, packet count, creation date
- **Protocol detection**: TCP, UDP, DNS, HTTP, TLS, ICMP, ARP

#### Packet Inspection
- **Detailed packet view** with nested layers:
  - Frame information (index, size, timestamp)
  - Ethernet/MAC layer (src/dst MAC, VLAN)
  - IP layer (IPv4/IPv6, addresses, TTL, flags)
  - Transport layer (TCP/UDP, ports, flags)
  - Application layer (HTTP, DNS, TLS, raw data)
  
#### Packet Type Detection
- **SYN** - TCP connection initiation
- **SYN-ACK** - Server acknowledgment
- **ACK** - General acknowledgment
- **FIN** - Connection termination request
- **RST** - Connection reset
- **PSH-ACK** - Data push with acknowledgment
- **UDP** - UDP datagram
- **ICMP** - Internet Control Message Protocol
- **DNS Query/Response** - Domain name lookups
- **HTTP Request/Response** - Web traffic
- **TLS Handshake** - Encrypted connection setup

#### Inline Editing
Edit packet fields directly in the UI:

**MAC Address Fields**
- Source MAC (Ethernet layer)
- Destination MAC (Ethernet layer)
- Format: `00:11:22:33:44:55`

**IP Address Fields**
- IPv4 Source/Destination
- IPv6 Source/Destination
- CIDR notation supported

**Port Fields**
- TCP/UDP source and destination ports
- Range: 0-65535

**VLAN Tagging**
- VLAN ID modification
- Priority level adjustment

**DNS Queries**
- Query name (domain)
- Record type (A, AAAA, MX, etc.)
- Response IPs for resolution

**HTTP Headers**
- Host field modification
- Regex-based replacement
- Auto-recalculation of checksums

**TLS SNI (Server Name Indication)**
- SNI hostname modification
- Binary-safe packet structure preservation
- Length field automatic updates

#### Checksum Recalculation
- **Automatic** after packet modification
- Supports: TCP, UDP, IPv4, IPv6
- Ensures packet validity

#### Download & Export
- Download modified PCAP files
- Original file preservation (creates `modified_*.pcap`)
- Multiple format support (PCAP, PCAPNG)

### Use Cases
- Network forensics and analysis
- Packet capture testing
- Protocol reverse engineering
- Traffic manipulation for testing
- Compliance auditing

---

## PCAP Generator 🎲

### Overview
Synthetic packet generator creating realistic traffic patterns with complete protocol flows.

### Key Features

#### Protocol Support

**TCP Flows**
- Full 3-way handshake (SYN, SYN-ACK, ACK)
- Data segments with PSH flag
- Graceful termination (FIN-ACK, ACK)
- 8-10 packets per flow
- Realistic sequence numbers and acknowledgments

**HTTP over TCP**
- HTTP GET requests
- HTTP 200 OK responses
- Complete TCP flow around HTTP
- Proper Content-Length headers
- Host header customization

**UDP Datagrams**
- Stateless UDP packets
- Custom payload support
- Multiple destination IPs

**DNS Queries (UDP)**
- A record queries (IPv4 resolution)
- AAAA record queries (IPv6 resolution)
- MX record queries (mail exchange)
- Proper DNS packet structure
- Query and response packets

**DNS over TCP**
- TCP-wrapped DNS queries
- For large DNS responses (>512 bytes)
- Firewall bypass scenarios

**TLS/SSL Handshake**
- TLS 1.2 Client Hello
- Server Hello response
- Certificate exchange
- Key exchange simulation
- Complete handshake flow

#### Network Configuration

**Configurable Parameters**
- Packet count (1-1000+)
- Source MAC address
- Destination MAC address
- Source IP address
- Destination IP address (auto-incremented per packet)
- Source port
- Destination port
- VLAN ID (optional)

**IP Addressing**
- IPv4 support with auto-increment
- IPv6 support with auto-increment
- Unique destination IP per flow
- Subnet calculation for ranges

**Protocol-Specific Options**
- HTTP Host header customization
- DNS query names and record types
- TLS SNI (Server Name Indication)
- TCP/UDP port configuration

#### Flow Generation
- Each generated packet gets **unique destination IP**
- Auto-incrementing using standard IP address arithmetic
- Realistic packet sequences and timing
- Proper TCP state machine simulation

### Output
- Generated PCAP file with timestamp
- Ready for immediate use
- Download or open in PCAP Editor
- File statistics displayed

### Use Cases
- Load testing network infrastructure
- Stress testing packet processing
- Training data generation
- Network simulation
- Protocol validation testing
- IDS/IPS testing scenarios

---

## PCAP Merger 🔀

### Overview
Multi-file PCAP consolidation tool for combining multiple capture files.

### Key Features

#### Multi-File Support
- Upload 2 or more PCAP/PCAPNG files simultaneously
- Drag-and-drop multi-select
- File validation before merge
- Size tracking per file

#### Merge Operations
- **Packet order preservation** - Chronological or sequential
- **Automatic timing** - Packets timestamped correctly
- **Format compatibility** - Handles mixed PCAP/PCAPNG formats
- **Lossless merge** - No packet data loss

#### Output Configuration
- **Default naming** - `merged_<timestamp>.pcap`
- **Custom naming** - User-specified output filename
- **Automatic location** - Saves to uploads folder
- **Size calculation** - Merged file statistics

#### Results Display
- Source files listed with packet counts
- Total merged packet count
- Merged file size
- Download option
- Open in PCAP Editor option

### Use Cases
- Consolidate multiple captures from same session
- Merge traffic from different network segments
- Combine test data from multiple sources
- Archive and compress captures
- Prepare data for analysis

---

## Hex Viewer 🔍

### Overview
Binary file inspection tool with dual-mode display and intelligent format detection.

### Key Features

#### File Upload
- **Any binary file** support (`.bin`, `.dat`, `.exe`, firmware, etc.)
- **Text files** with automatic encoding detection
- **File size** indicator and validation
- **Progress tracking** during upload

#### Dual-Mode Display

**Text View (Default)**
- Human-readable format when possible
- Automatic encoding detection
- Syntax highlighting for structured formats
- Color-coded file type indicator

**Hex View**
- Traditional hex dump format
- 16 bytes per row layout
- Offset column (00000000, 00000010, etc.)
- ASCII column for readable characters
- Pagination for large files

#### Format Detection

**Automatic Format Identification**:
- **JSON** - Code syntax highlighting (green indicator)
- **XML** - Markup syntax highlighting (orange indicator)
- **Plain Text** - Standard text display (blue indicator)
- **Binary** - Hex dump only (gray indicator)

#### Encoding Support
- **UTF-8** - Default, most common
- **ASCII** - 7-bit ASCII text
- **Latin-1 (ISO-8859-1)** - Western European
- **UTF-16** - Unicode wide characters
- **UTF-32** - 4-byte Unicode

**Auto-detection Logic**:
1. Attempts UTF-8 decoding
2. Falls back to ASCII
3. Tries Latin-1
4. Tests UTF-16 and UTF-32
5. Shows as binary if <70% printable

#### Search Functionality
- **Hex pattern search** - Find byte sequences
- **ASCII text search** - Find readable strings
- **Case-sensitive/insensitive** options
- **Search results highlighting** - Jump to match
- **Full file search** - Across entire document

#### Navigation
- **Pagination** - Large files split into pages
- **Jump to offset** - Direct byte position access
- **Scroll preservation** - Position maintained
- **Result highlighting** - Visual match indicators

#### Export Features
- **Download as text** - Extract readable content
- **Hex dump export** - Save hex representation
- **Copy to clipboard** - Single-click copy
- **Format preservation** - Original bytes preserved

#### Large File Support
- Efficient pagination (1000-5000 bytes per page)
- No file size limitations
- Streaming display
- Memory-efficient rendering

### File Type Examples

**JSON Files**
```json
{
  "name": "example",
  "value": 123
}
```
✅ Displayed with syntax highlighting

**XML Files**
```xml
<?xml version="1.0"?>
<root>
  <element>data</element>
</root>
```
✅ Displayed with markup highlighting

**Binary Files**
```
00000000: 89 50 4e 47 0d 0a 1a 0a  ..PNG...
00000008: 00 00 00 0d 49 48 44 52  ....IHDR
```
✅ Displayed in hex format

### Use Cases
- Firmware analysis and validation
- Protocol packet inspection
- File corruption diagnosis
- Binary file reverse engineering
- Encoding verification
- Data recovery and forensics
- Security research
- File format specification testing

---

## Common Workflows

### Workflow 1: Generate → Edit → Download

1. **PCAP Generator** → Create test traffic
2. **PCAP Editor** → Modify specific packets
3. Download modified PCAP for testing

### Workflow 2: Merge → Analyze → Export

1. **PCAP Merger** → Combine captures
2. **PCAP Editor** → Analyze merged traffic
3. **Hex Viewer** → Inspect packet payloads
4. Download for external analysis

### Workflow 3: Forensics → Investigation

1. **PCAP Editor** → Load evidence
2. **PCAP Generator** → Create comparison traffic
3. **Hex Viewer** → Deep-dive binary analysis
4. Document findings

---

## Advanced Tips

### Performance
- Keep PCAP files under 500MB for smooth performance
- Use PCAP Merger to split large files if needed
- Enable pagination for large hex views

### Security
- Don't upload sensitive PCAP files publicly
- Use HTTPS in production deployment
- Validate uploaded files on backend
- Implement file retention policies

### Integration
- API endpoints available at `/api/*`
- Programmatic file upload supported
- JSON response format for all operations
- CORS enabled for cross-origin requests

---

**Master all features and become a packet analysis expert! 🚀**