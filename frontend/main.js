import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

const app = createApp(App)

// Configure axios
axios.defaults.baseURL = 'http://localhost:5000/api'
app.config.globalProperties.$axios = axios

app.use(router)
app.mount('#app')
