import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

const app = createApp(App)

// Configure axios
// axios.defaults.baseURL = 'http://localhost:5000/api'
// Use Vite environment variable, fallback to '/api' for Vercel pointing
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
app.config.globalProperties.$axios = axios

app.use(router)
app.mount('#app')
