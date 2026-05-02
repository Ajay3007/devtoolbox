/* Root App — wires shell + views + tweaks */

const DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "accent": "#7cf9a4",
  "density": "comfortable",
  "fontMix": "inter-mono"
}/*EDITMODE-END*/;

const ACCENT_OPTIONS = [
  { k: '#7cf9a4', l: 'green' },
  { k: '#58c0ff', l: 'blue' },
  { k: '#ffb454', l: 'amber' },
  { k: '#ff6a8a', l: 'pink' },
  { k: '#c792ea', l: 'purple' },
];

function App() {
  const [view, setView] = React.useState('overview');
  const [tweaks, setTweaks] = useTweaks(DEFAULTS);

  React.useEffect(() => {
    document.documentElement.classList.toggle('light', tweaks.theme === 'light');
    document.documentElement.style.setProperty('--accent', tweaks.accent);
    document.documentElement.style.setProperty('--density', tweaks.density === 'compact' ? 0.88 : 1);
    document.body.style.fontSize = tweaks.density === 'compact' ? '13px' : '14px';
  }, [tweaks]);

  const ViewComponent = {
    overview: OverviewView,
    editor: PCAPEditorView,
    generator: PCAPGeneratorView,
    merger: PCAPMergerView,
    hex: HexView,
    files: FilesView,
    pdf: PDFView,
    usecases: UseCasesView,
  }[view] || OverviewView;

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <LeftRail current={view} onNav={setView}/>
      <div style={{ marginLeft: 232, flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <TopBar current={view}/>
        <main style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }} data-screen-label={view}>
          <div key={view} style={{ animation: 'slideIn 0.3s ease-out', flex: 1, display: 'flex', flexDirection: 'column' }}>
            <ViewComponent onNav={setView}/>
          </div>
        </main>
      </div>

      <TweaksPanel>
        <TweakSection title="Theme">
          <TweakRadio
            value={tweaks.theme}
            options={[{value:'dark',label:'Dark'},{value:'light',label:'Light'}]}
            onChange={v => setTweaks({ theme: v })}
          />
        </TweakSection>
        <TweakSection title="Accent">
          <div style={{ display: 'flex', gap: 8 }}>
            {ACCENT_OPTIONS.map(a => (
              <button key={a.k} onClick={() => setTweaks({ accent: a.k })}
                title={a.l}
                style={{
                  width: 26, height: 26, borderRadius: 6,
                  background: a.k,
                  border: tweaks.accent === a.k ? '2px solid var(--text)' : '2px solid var(--line)',
                  cursor: 'pointer',
                }}/>
            ))}
          </div>
        </TweakSection>
        <TweakSection title="Density">
          <TweakRadio
            value={tweaks.density}
            options={[{value:'comfortable',label:'Comfortable'},{value:'compact',label:'Compact'}]}
            onChange={v => setTweaks({ density: v })}
          />
        </TweakSection>
        <TweakSection title="Jump to tool">
          <TweakSelect
            value={view}
            options={NAV_ITEMS.filter(n=>n.badge!=='soon').map(n=>({value:n.id,label:n.label}))}
            onChange={setView}
          />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
