<template>
  <div id="app" class="app-container">
    <header class="app-header">
      <h1>DevToolBox</h1>
      <nav>
        <router-link to="/">Home</router-link>
        <router-link to="/pcap-editor">PCAP Editor</router-link>
        <router-link to="/pcap-generator">PCAP Generator</router-link>
        <router-link to="/pcap-merger">PCAP Merger</router-link>
        <router-link to="/hex-viewer">Hex Viewer</router-link>
        <router-link to="/file-manager">📂 Files</router-link>
        <router-link to="/pdf-editor">📄 PDF Editor</router-link>
      </nav>
    </header>
    <main>
      <router-view></router-view>
    </main>
    <footer class="app-footer">
      <p>&copy; 2025 DevToolBox. All rights reserved.</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f5f5f5;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.app-header nav {
  display: flex;
  gap: 2rem;
}

.app-header nav a {
  color: white;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.3s;
}

.app-header nav a:hover {
  opacity: 0.8;
}

.app-header nav a.router-link-active {
  border-bottom: 2px solid white;
  padding-bottom: 0.25rem;
}

main {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background: #333;
  color: white;
  text-align: center;
  padding: 1.5rem;
  margin-top: auto;
}

@media (max-width: 768px) {
  .app-header h1 {
    font-size: 1.5rem;
  }

  .app-header nav {
    flex-direction: column;
    gap: 0.5rem;
  }

  main {
    padding: 1rem;
  }
}
</style>
