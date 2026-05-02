import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import PCAPEditor from '../views/PCAPEditor.vue'
import PCAPGenerator from '../views/PCAPGenerator.vue'
import PCAPMerger from '../views/PCAPMerger.vue'
import HexViewer from '../views/HexViewer.vue'
import FileManager from '../views/FileManager.vue'
import PDFEditor from '../views/PDFEditor.vue'
import ReceiptEditor from '../views/ReceiptEditor.vue'
import UseCases from '../views/UseCases.vue'

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
  },
  {
    path: '/file-manager',
    name: 'file-manager',
    component: FileManager
  },
  {
    path: '/pdf-editor',
    name: 'pdf-editor',
    component: PDFEditor
  },
  {
    path: '/receipt-editor',
    name: 'receipt-editor',
    component: ReceiptEditor
  },
  {
    path: '/use-cases',
    name: 'use-cases',
    component: UseCases
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
