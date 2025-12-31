import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import PCAPEditor from '../views/PCAPEditor.vue'
import PCAPGenerator from '../views/PCAPGenerator.vue'
import PCAPMerger from '../views/PCAPMerger.vue'
import HexViewer from '../views/HexViewer.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/pcap-editor',
    name: 'pcap-editor',
    component: PCAPEditor
    },
    {
      path: '/pcap-generator',
      name: 'pcap-generator',
      component: PCAPGenerator
  },
  {
    path: '/pcap-merger',
    name: 'pcap-merger',
    component: PCAPMerger
  },
  {
    path: '/hex-viewer',
    name: 'hex-viewer',
    component: HexViewer
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
