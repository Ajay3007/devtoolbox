<template>
  <div class="home-container">
    <section class="hero">
      <h1>Welcome to DevToolBox</h1>
      <p>Powerful tools for data plane developers and software engineers</p>
      <div class="cta-buttons">
        <router-link to="/pcap-editor" class="btn btn-primary">PCAP Editor</router-link>
        <router-link to="/pcap-generator" class="btn btn-primary">PCAP Generator</router-link>
        <router-link to="/pcap-merger" class="btn btn-primary">PCAP Merger</router-link>
        <router-link to="/hex-viewer" class="btn btn-primary">Hex Viewer</router-link>
        <a href="#tools" class="btn btn-secondary">Learn More</a>
      </div>
    </section>

    <section id="tools" class="tools-section">
      <h2>Available Tools</h2>
      <div class="tools-grid">
        <div class="tool-card">
          <div class="tool-icon">📦</div>
          <h3>PCAP Editor</h3>
          <p>Create, read, and modify PCAP dumps with advanced payload editing capabilities.</p>
          <router-link to="/pcap-editor">Get Started →</router-link>
        </div>

        <div class="tool-card">
          <div class="tool-icon">🔧</div>
          <h3>PCAP Generator</h3>
          <p>Generate PCAP files with various protocols: TCP, HTTP, UDP, DNS, TLS with custom configurations.</p>
          <router-link to="/pcap-generator">Get Started →</router-link>
        </div>

        <div class="tool-card">
          <div class="tool-icon">🧩</div>
          <h3>PCAP Merger</h3>
          <p>Merge two or more PCAP/PCAPNG files into a single capture for streamlined analysis.</p>
          <router-link to="/pcap-merger">Get Started →</router-link>
        </div>

        <div class="tool-card">
          <div class="tool-icon">🔍</div>
          <h3>Hex Viewer</h3>
          <p>Advanced binary file inspection and hexadecimal analysis with search functionality.</p>
          <router-link to="/hex-viewer">Get Started →</router-link>
        </div>

        <div class="tool-card">
          <div class="tool-icon">📂</div>
          <h3>File Manager</h3>
          <p>Browse, rename, download and delete all files in the uploads folder from one place.</p>
          <router-link to="/file-manager">Get Started →</router-link>
        </div>

        <div class="tool-card">
          <div class="tool-icon">📄</div>
          <h3>PDF Editor</h3>
          <p>Click on any text in a PDF to edit it in-place while preserving font size and style.</p>
          <router-link to="/pdf-editor">Get Started →</router-link>
        </div>

        <div class="tool-card">
          <div class="tool-icon">📊</div>
          <h3>Log Analyzer</h3>
          <p>Parse and analyze logs for patterns and insights (Coming Soon)</p>
          <a href="#" disabled>Coming Soon</a>
        </div>
      </div>
    </section>

    <section class="features-section">
      <h2>Key Features</h2>
      <ul class="features-list">
        <li>🚀 Web-based interface - No installation required</li>
        <li>⚙️ Powerful backend API for complex operations</li>
        <li>📦 Support for PCAP and PCAPNG formats</li>
        <li>✏️ Advanced payload modification capabilities</li>
        <li>📊 Detailed packet and file statistics</li>
        <li>🔄 Import/Export functionality</li>
      </ul>
    </section>
  </div>
</template>

<script>
export default {
  name: 'Home',
  data() {
    return {}
  }
}
</script>

<style scoped>
.home-container {
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4rem 2rem;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 4rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.hero h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.hero p {
  font-size: 1.25rem;
  margin-bottom: 2rem;
  opacity: 0.95;
}

.cta-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
  border: none;
  cursor: pointer;
  font-size: 1rem;
}

.btn-primary {
  background: white;
  color: #667eea;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid white;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.3);
}

.tools-section {
  margin-bottom: 4rem;
}

.tools-section h2,
.features-section h2 {
  font-size: 2rem;
  margin-bottom: 2rem;
  color: #333;
  text-align: center;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.tool-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  text-align: center;
  transition: all 0.3s;
}

.tool-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.tool-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.tool-card h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #667eea;
}

.tool-card p {
  color: #666;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.tool-card a {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  transition: all 0.3s;
}

.tool-card a:hover:not([disabled]) {
  background: #764ba2;
  transform: translateX(4px);
}

.tool-card a[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}

.features-section {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.features-list {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.features-list li {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  line-height: 1.6;
  color: #333;
  font-size: 1.05rem;
}

@media (max-width: 768px) {
  .hero {
    padding: 2rem 1rem;
  }

  .hero h1 {
    font-size: 2rem;
  }

  .hero p {
    font-size: 1rem;
  }

  .cta-buttons {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>
