# Contributing to DevToolBox 🤝

Thank you for your interest in contributing! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and professional. We're building this together!

---

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- Git
- Familiarity with Flask and Vue.js (helpful but not required)

### Setup Development Environment

1. **Fork the repository**
   - Click "Fork" on GitHub
   - Clone your fork: `git clone https://github.com/YOUR_USERNAME/devtoolbox.git`

2. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Setup as per** [INSTALLATION.md](INSTALLATION.md)

4. **Create a branch** for your work:
   ```bash
   git checkout -b feature/amazing-feature
   ```

---

## Development Workflow

### Backend Development

**File Structure**:
```
backend/
├── app.py              # Flask application
├── pcap_handler.py     # PCAP processing logic
├── utils.py            # Utility functions
├── requirements.txt    # Dependencies
└── uploads/            # File storage
```

### Adding a New Backend Endpoint

1. **Define the endpoint in** `backend/app.py`:
```python
@app.route('/api/my-tool/process', methods=['POST'])
def process_data():
    """Process data using my tool"""
    try:
        file = request.files.get('file')
        if not file:
            return make_response({
                'success': False,
                'status_code': 400,
                'data': {'message': 'No file provided'}
            }, 400)
        
        # Process file
        result = process_with_my_tool(file)
        
        return make_response({
            'success': True,
            'status_code': 200,
            'data': result
        }, 200)
    
    except Exception as e:
        return make_response({
            'success': False,
            'status_code': 500,
            'data': {'message': str(e)}
        }, 500)
```

2. **If needed, add method to** `backend/pcap_handler.py`:
```python
class PCAPHandler:
    def process_with_my_tool(self, filepath, options=None):
        """Description of what this does"""
        try:
            # Implementation
            return result
        except Exception as e:
            raise Exception(f"Processing failed: {str(e)}")
```

3. **Test the endpoint**:
```bash
curl -X POST \
  -F "file=@testfile.pcap" \
  http://localhost:5000/api/my-tool/process
```

### Frontend Development

**File Structure**:
```
frontend/
├── views/              # Page components
│   ├── Home.vue
│   ├── PCAPEditor.vue
│   ├── PCAPGenerator.vue
│   ├── PCAPMerger.vue
│   └── HexViewer.vue
├── router/
│   └── index.js        # Route definitions
├── App.vue             # Root component
├── main.js             # Entry point
└── vite.config.js      # Vite configuration
```

### Adding a New Frontend Tool

1. **Create new component** in `frontend/views/NewTool.vue`:
```vue
<template>
  <div class="container">
    <h2>New Tool</h2>
    <input type="file" @change="handleFileUpload" />
    <button @click="processTool">Process</button>
    <div v-if="loading" class="spinner">Loading...</div>
    <div v-if="result" class="result">{{ result }}</div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      file: null,
      loading: false,
      result: null,
      error: null
    };
  },
  methods: {
    handleFileUpload(event) {
      this.file = event.target.files[0];
    },
    async processTool() {
      this.loading = true;
      const formData = new FormData();
      formData.append('file', this.file);
      
      try {
        const response = await axios.post(
          'http://localhost:5000/api/my-tool/process',
          formData
        );
        this.result = response.data.data;
      } catch (error) {
        this.error = error.response?.data?.data?.message || 'Error';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.container {
  padding: 20px;
}
.spinner {
  text-align: center;
}
.result {
  margin-top: 20px;
  padding: 10px;
  background: #f0f0f0;
  border-radius: 4px;
}
</style>
```

2. **Add route** in `frontend/router/index.js`:
```javascript
{
  path: '/new-tool',
  component: () => import('../views/NewTool.vue')
}
```

3. **Add navigation link** in `frontend/App.vue`:
```vue
<router-link to="/new-tool">New Tool</router-link>
```

4. **Test in browser** at `http://localhost:8080`

---

## Coding Standards

### Python (Backend)

**Style**:
- Follow PEP 8 conventions
- Use 4 spaces for indentation
- Max line length: 100 characters
- Use type hints where helpful

**Example**:
```python
def modify_packet(filepath: str, packet_index: int, field: str, value: str) -> dict:
    """
    Modify a packet field in a PCAP file.
    
    Args:
        filepath: Path to PCAP file
        packet_index: Index of packet to modify
        field: Field path (e.g., 'layers.eth.src_mac')
        value: New value for field
        
    Returns:
        dict: Result with success status and modified file path
    """
    # Implementation
    pass
```

**Error Handling**:
```python
try:
    result = process_data(data)
except ValueError as e:
    return {'success': False, 'message': f'Validation error: {str(e)}'}
except Exception as e:
    return {'success': False, 'message': 'Internal error'}
```

### JavaScript/Vue (Frontend)

**Style**:
- Use 2 spaces for indentation
- Use `const`/`let`, avoid `var`
- Use arrow functions `() => {}`
- Add comments for complex logic

**Example**:
```javascript
// Method to upload file
async uploadFile(file) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post('/api/endpoint', formData);
    this.processedData = response.data;
  } catch (error) {
    console.error('Upload failed:', error);
    this.error = 'File upload failed';
  }
}
```

---

## Testing

### Manual Testing

**Backend**:
```bash
# Test endpoint with curl
curl -X POST \
  -F "file=@test.pcap" \
  http://localhost:5000/api/endpoint

# Or test with Python
python
from scapy.all import rdpcap
packets = rdpcap('test.pcap')
print(f"Loaded {len(packets)} packets")
```

**Frontend**:
1. Open browser DevTools (F12)
2. Check Console for errors
3. Check Network tab for API responses
4. Test with different inputs

### Writing Tests

Create `tests/test_pcap_handler.py`:
```python
import unittest
from backend.pcap_handler import PCAPHandler

class TestPCAPHandler(unittest.TestCase):
    def setUp(self):
        self.handler = PCAPHandler('backend/uploads')
    
    def test_merge_pcaps(self):
        # Test merge functionality
        result = self.handler.merge_pcaps(['file1.pcap', 'file2.pcap'])
        self.assertIsNotNone(result)
        self.assertGreater(result['packet_count'], 0)

if __name__ == '__main__':
    unittest.main()
```

Run tests:
```bash
cd backend
python -m unittest discover tests
```

---

## Documentation

### Adding Comments

```python
# Python
def complex_function(data):
    """
    Brief description of what this does.
    
    Args:
        data (dict): Input data structure
        
    Returns:
        dict: Result with 'success' and 'data' keys
        
    Raises:
        ValueError: If data format invalid
    """
    # Complex logic explanation
    pass
```

```javascript
// JavaScript
/**
 * Brief description of what this does.
 * @param {File} file - The file to process
 * @returns {Promise<Object>} Result object
 */
async function processFile(file) {
  // Implementation
}
```

### Updating Documentation

1. Update relevant `.md` file:
   - [FEATURES.md](FEATURES.md) - For new features
   - [API_REFERENCE.md](API_REFERENCE.md) - For new endpoints
   - [README.md](README.md) - For major changes

2. Include examples and use cases

3. Keep documentation up-to-date with code

---

## Commit Messages

Follow conventional commit format:

```
feat(pcap): add TCP flow generation
^   ^      ^
│   │      └─ Description
│   └─────── Component
└─────────── Type
```

**Types**:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting
- `refactor` - Code restructuring
- `test` - Tests
- `chore` - Dependencies, build

**Examples**:
```
feat(hex-viewer): add search functionality
fix(pcap-editor): resolve checksum calculation error
docs(api): update endpoint documentation
```

---

## Pull Request Process

1. **Create descriptive PR title**:
   - ❌ "Update stuff"
   - ✅ "Add packet type detection to PCAP Editor"

2. **Write PR description**:
   ```markdown
   ## Description
   Adds packet type detection showing SYN, SYN-ACK, etc.
   
   ## Changes
   - Added _get_packet_type() method in PCAPHandler
   - Updated frontend to display packet type field
   - Added type detection for all protocols
   
   ## Testing
   - Tested with TCP, UDP, DNS, HTTP packets
   - Verified all packet types display correctly
   
   ## Screenshots
   [Include if UI changes]
   ```

3. **Ensure tests pass**:
   ```bash
   # Backend
   cd backend
   python -m unittest discover
   
   # Frontend
   cd frontend
   npm run lint
   ```

4. **Code review**:
   - Respond to feedback promptly
   - Make requested changes
   - Push updates to same branch

---

## Areas for Contribution

### Beginner-Friendly
- ✅ Documentation improvements
- ✅ Bug fixes (marked as "good first issue")
- ✅ UI/UX enhancements
- ✅ Test coverage

### Intermediate
- ✅ New packet analysis features
- ✅ Protocol support (new packet types)
- ✅ Performance optimization
- ✅ Error handling improvements

### Advanced
- ✅ New tools/utilities
- ✅ Architecture improvements
- ✅ Plugin system
- ✅ Database integration

---

## Release Process

1. **Version numbering**: MAJOR.MINOR.PATCH
   - `1.0.0` - Major features
   - `1.1.0` - Minor features
   - `1.0.1` - Bug fixes

2. **Update version**:
   - `backend/app.py`: `VERSION = "1.1.0"`
   - `frontend/package.json`: `"version": "1.1.0"`

3. **Update CHANGELOG.md**:
   ```markdown
   ## [1.1.0] - 2024-01-15
   
   ### Added
   - New feature X
   - New feature Y
   
   ### Fixed
   - Bug fix A
   - Bug fix B
   ```

4. **Create GitHub release**:
   - Tag commit: `git tag v1.1.0`
   - Create release notes
   - Attach binaries if applicable

---

## Getting Help

- **Questions**: Open GitHub Discussion
- **Bugs**: Open GitHub Issue with details
- **Features**: Discuss in Issues before implementing
- **Documentation**: Ask in Discussions

---

## Code Review Checklist

When reviewing PRs, check:

- [ ] Code follows style guidelines
- [ ] Comments explain complex logic
- [ ] No console.log or debug code
- [ ] Error handling is proper
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Performance acceptable
- [ ] Security considerations addressed

---

## Development Tips

### Debug Backend
```python
# Add logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Variable value: {variable}")
```

### Debug Frontend
```javascript
// Use Vue DevTools
// Open DevTools: F12
// Console tab for errors
// Network tab for API calls
// Vue tab for component state

console.log('Debug:', this.data);
console.table(this.array);
```

### Hot Reload
- Frontend: Automatic with Vite
- Backend: Restart Flask server manually (or add `--reload`)

---

## License

By contributing, you agree your code is licensed under MIT License.

---

## Thank You!

Your contributions make DevToolBox better for everyone! 🎉

---

**Happy contributing! Feel free to reach out with questions.** 🚀