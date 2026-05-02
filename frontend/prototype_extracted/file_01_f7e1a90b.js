/* Custom mono line icons. 20x20, stroke 1.5 */
const Icon = ({ children, size = 18, stroke = 1.5, style }) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none"
       stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round"
       style={style}>
    {children}
  </svg>
);

const IconHome = (p) => <Icon {...p}><path d="M3 9 10 3l7 6"/><path d="M5 8v9h10V8"/></Icon>;
const IconEditor = (p) => <Icon {...p}>
  <rect x="2.5" y="4" width="15" height="12" rx="1.2"/>
  <path d="M2.5 8h15"/>
  <path d="M5.5 11.5h3M5.5 13.5h5"/>
  <circle cx="13.5" cy="12.5" r="1.5"/>
</Icon>;
const IconGenerator = (p) => <Icon {...p}>
  <path d="M4 10h3l1-3 2 6 1-3h5"/>
  <circle cx="4" cy="10" r="1.2"/>
  <circle cx="16" cy="10" r="1.2"/>
</Icon>;
const IconMerger = (p) => <Icon {...p}>
  <path d="M3 5l4 4v2l-4 4"/>
  <path d="M17 5l-4 4v2l4 4"/>
  <circle cx="10" cy="10" r="1.4"/>
</Icon>;
const IconHex = (p) => <Icon {...p}>
  <path d="M10 2.5l6.5 3.75v7.5L10 17.5 3.5 13.75v-7.5z"/>
  <path d="M7.5 8v4M10 8v4M12.5 8v4"/>
</Icon>;
const IconFiles = (p) => <Icon {...p}>
  <path d="M2.5 5.5a1 1 0 0 1 1-1h3.5l1.5 2h7a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1h-12a1 1 0 0 1-1-1z"/>
</Icon>;
const IconPDF = (p) => <Icon {...p}>
  <path d="M5 2.5h7l3.5 3.5v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-13a1 1 0 0 1 1-1z"/>
  <path d="M12 2.5V6h3.5"/>
  <path d="M7 11h6M7 13.5h4"/>
</Icon>;
const IconLog = (p) => <Icon {...p}>
  <path d="M3 15l3-4 3 2 3-6 3 4 2-2"/>
  <path d="M3 17h14"/>
</Icon>;
const IconUseCases = (p) => <Icon {...p}>
  <circle cx="10" cy="7" r="2.5"/>
  <path d="M4 16.5c.7-2.8 3.1-4.5 6-4.5s5.3 1.7 6 4.5"/>
</Icon>;
const IconUpload = (p) => <Icon {...p}>
  <path d="M10 13V4"/><path d="M6 8l4-4 4 4"/><path d="M3 15v2h14v-2"/>
</Icon>;
const IconDownload = (p) => <Icon {...p}>
  <path d="M10 4v9"/><path d="M6 9l4 4 4-4"/><path d="M3 15v2h14v-2"/>
</Icon>;
const IconPlay = (p) => <Icon {...p}><path d="M5 3.5v13l11-6.5z" fill="currentColor"/></Icon>;
const IconPause = (p) => <Icon {...p}><path d="M6 4v12M14 4v12"/></Icon>;
const IconSearch = (p) => <Icon {...p}><circle cx="9" cy="9" r="5"/><path d="m13 13 4 4"/></Icon>;
const IconChevR = (p) => <Icon {...p}><path d="m7 4 6 6-6 6"/></Icon>;
const IconChevD = (p) => <Icon {...p}><path d="m4 7 6 6 6-6"/></Icon>;
const IconDot = (p) => <Icon {...p}><circle cx="10" cy="10" r="2.2" fill="currentColor"/></Icon>;
const IconCheck = (p) => <Icon {...p}><path d="m4 10 4 4 8-9"/></Icon>;
const IconX = (p) => <Icon {...p}><path d="m5 5 10 10M15 5 5 15"/></Icon>;
const IconCopy = (p) => <Icon {...p}>
  <rect x="4" y="6" width="10" height="11" rx="1"/>
  <path d="M6 6V4a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1h-2"/>
</Icon>;
const IconFilter = (p) => <Icon {...p}><path d="M3 4h14l-5 7v5l-4-2v-3z"/></Icon>;
const IconFlow = (p) => <Icon {...p}>
  <rect x="2" y="4" width="5" height="4" rx="1"/>
  <rect x="13" y="4" width="5" height="4" rx="1"/>
  <rect x="7.5" y="12" width="5" height="4" rx="1"/>
  <path d="M7 6h6M5 8v4h4M15 8v4h-4"/>
</Icon>;

Object.assign(window, {
  Icon, IconHome, IconEditor, IconGenerator, IconMerger, IconHex,
  IconFiles, IconPDF, IconLog, IconUseCases, IconUpload, IconDownload,
  IconPlay, IconPause, IconSearch, IconChevR, IconChevD, IconDot,
  IconCheck, IconX, IconCopy, IconFilter, IconFlow
});
