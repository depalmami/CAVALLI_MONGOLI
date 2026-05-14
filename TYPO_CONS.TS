import React, { useState, useRef, useEffect } from 'react';
import { Download, Type, Zap, Sliders, Plus, Trash2, Layers, Grid, Shuffle, RotateCcw, Box, Sparkles, Wind, Copy, Palette, Archive, Loader2, Settings2, X } from 'lucide-react';

const App = () => {
  // --- State Management ---
  const [text, setText] = useState("CAVALLI MONGOLI");
  const [embedCode, setEmbedCode] = useState("");
  const [editingId, setEditingId] = useState(null);
  
  const [loadedFonts, setLoadedFonts] = useState([{ 
    name: 'sans-serif', 
    id: 'default', 
    customColor: null,
    customGlow: null,
    customGlowColor: null,
    customStroke: null,
    customStrokeColor: null,
    customBlur: null,
    customSkew: null,
    customFontSize: null,
    customLetterSpacing: null
  }]);
  
  // App State
  const [isDownloadingAll, setIsDownloadingAll] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);

  // Global Controls (Master)
  const [fontSize, setFontSize] = useState(60);
  const [globalColor, setGlobalColor] = useState("#ffffff");
  const [letterSpacing, setLetterSpacing] = useState(0);
  const [glowStrength, setGlowStrength] = useState(0);
  const [glowColor, setGlowColor] = useState("#ff0000");
  const [strokeWidth, setStrokeWidth] = useState(0);
  const [strokeColor, setStrokeColor] = useState("#000000");
  const [blurAmount, setBlurAmount] = useState(0);
  const [skewAmount, setSkewAmount] = useState(0);
  const [isGlitch, setIsGlitch] = useState(false);
  const [is3D, setIs3D] = useState(false);
  const [hasReflection, setHasReflection] = useState(false);
  
  const canvasRef = useRef(null);

  // --- Helpers ---
  const getRandomColor = () => {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
      color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
  };

  const getRandomInt = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

  // --- Font Parser & Loader ---
  const handleLoadFonts = () => {
    if (!embedCode.trim()) return;

    const hrefRegex = /href="([^"]+)"/g;
    let match;
    const urls = [];
    while ((match = hrefRegex.exec(embedCode)) !== null) {
      if (match[1].includes('fonts.googleapis.com')) {
        urls.push(match[1]);
      }
    }

    if (urls.length === 0) {
      const urlRegex = /(https:\/\/fonts\.googleapis\.com\/css2\?[^"\s]+)/g;
      const foundUrls = embedCode.match(urlRegex);
      if (foundUrls) urls.push(...foundUrls);
    }

    const newFonts = [...loadedFonts];
    urls.forEach(url => {
      if (!document.querySelector(`link[href="${url}"]`)) {
        const link = document.createElement('link');
        link.href = url;
        link.rel = 'stylesheet';
        document.head.appendChild(link);
      }
      try {
        const urlObj = new URL(url);
        const families = urlObj.searchParams.getAll('family');
        families.forEach(f => {
          const name = f.split(':')[0].replace(/\+/g, ' ');
          if (!newFonts.find(nf => nf.name === name)) {
            newFonts.push({ 
              name, 
              id: Math.random().toString(36).substr(2, 9), 
              customColor: null,
              customGlow: null,
              customGlowColor: null,
              customStroke: null,
              customStrokeColor: null,
              customBlur: null,
              customSkew: null,
              customFontSize: null,
              customLetterSpacing: null
            });
          }
        });
      } catch (e) {}
    });

    setLoadedFonts(newFonts);
    setEmbedCode("");
  };

  const randomizeAllEverything = () => {
    setLoadedFonts(loadedFonts.map(f => ({ 
      ...f, 
      customColor: getRandomColor(),
      customGlow: getRandomInt(0, 80),
      customGlowColor: getRandomColor(),
      customStroke: getRandomInt(0, 15),
      customStrokeColor: getRandomColor(),
      customBlur: getRandomInt(0, 10),
      customSkew: getRandomInt(-30, 30),
    })));
  };

  const randomizeSingleEverything = (id) => {
    setLoadedFonts(loadedFonts.map(f => f.id === id ? { 
      ...f, 
      customColor: getRandomColor(),
      customGlow: getRandomInt(0, 80),
      customGlowColor: getRandomColor(),
      customStroke: getRandomInt(0, 15),
      customStrokeColor: getRandomColor(),
      customBlur: getRandomInt(0, 10),
      customSkew: getRandomInt(-30, 30),
    } : f));
  };

  const resetSingleEverything = (id) => {
    setLoadedFonts(loadedFonts.map(f => f.id === id ? { 
      ...f, 
      customColor: null,
      customGlow: null,
      customGlowColor: null,
      customStroke: null,
      customStrokeColor: null,
      customBlur: null,
      customSkew: null,
      customFontSize: null,
      customLetterSpacing: null
    } : f));
  };

  const updateIndividualParam = (id, param, value) => {
    setLoadedFonts(loadedFonts.map(f => f.id === id ? { ...f, [param]: value } : f));
  };

  const removeFont = (id) => {
    if (id === 'default') return;
    setLoadedFonts(loadedFonts.filter(f => f.id !== id));
  };

  // --- Universal Download Logic ---
  const downloadFontImage = (font) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = 2400; 
    const h = 600;
    canvas.width = w;
    canvas.height = h;

    const activeColor = font.customColor || globalColor;
    const activeGlow = font.customGlow !== null ? font.customGlow : glowStrength;
    const activeGlowColor = font.customGlowColor || glowColor;
    const activeStroke = font.customStroke !== null ? font.customStroke : strokeWidth;
    const activeStrokeColor = font.customStrokeColor || strokeColor;
    const activeFontSize = font.customFontSize !== null ? font.customFontSize : fontSize;
    const activeSpacing = font.customLetterSpacing !== null ? font.customLetterSpacing : letterSpacing;
    const activeBlur = font.customBlur !== null ? font.customBlur : blurAmount;
    const activeSkew = font.customSkew !== null ? font.customSkew : skewAmount;

    ctx.clearRect(0, 0, w, h);
    ctx.save();
    
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = `${activeFontSize * 2.5}px "${font.name}", sans-serif`;
    
    if ('letterSpacing' in ctx) {
      ctx.letterSpacing = `${activeSpacing * 2.5}px`;
    }

    if (activeBlur > 0) ctx.filter = `blur(${activeBlur * 2}px)`;
    
    ctx.translate(w / 2, h / 2);
    if (activeSkew !== 0) ctx.transform(1, 0, Math.tan(activeSkew * Math.PI / 180), 1, 0, 0);

    if (is3D) {
      ctx.save();
      for (let i = 18; i > 0; i--) {
        ctx.fillStyle = `rgba(0,0,0,${0.1 * (1 - i/18)})`;
        ctx.fillText(text, i, i);
      }
      ctx.restore();
    }

    if (activeGlow > 0) {
      ctx.shadowBlur = activeGlow * 3;
      ctx.shadowColor = activeGlowColor;
    }

    if (activeStroke > 0) {
      ctx.strokeStyle = activeStrokeColor;
      ctx.lineWidth = activeStroke * 2.5;
      ctx.lineJoin = 'round';
      ctx.strokeText(text, 0, 0);
    }

    ctx.fillStyle = activeColor;
    ctx.fillText(text, 0, 0);

    ctx.restore();

    const fileName = `${text.substring(0,20).replace(/[^a-z0-9]/gi, '_')}_${font.name.replace(/\s+/g, '_')}.png`;
    const link = document.createElement('a');
    link.download = fileName;
    link.href = canvas.toDataURL('image/png');
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadAll = async () => {
    if (isDownloadingAll) return;
    setIsDownloadingAll(true);
    setDownloadProgress(0);

    for (let i = 0; i < loadedFonts.length; i++) {
      const font = loadedFonts[i];
      downloadFontImage(font);
      setDownloadProgress(Math.round(((i + 1) / loadedFonts.length) * 100));
      await new Promise(resolve => setTimeout(resolve, 800));
    }

    setIsDownloadingAll(false);
  };

  // Find font currently being edited
  const editingFont = loadedFonts.find(f => f.id === editingId);

  return (
    <div className="flex flex-col lg:flex-row min-h-screen bg-black text-zinc-100 font-sans selection:bg-red-500/30">
      <canvas ref={canvasRef} className="hidden" />

      {/* --- Sidebar (Master Controls) --- */}
      <aside className="w-full lg:w-[400px] bg-zinc-950 border-r border-zinc-900 p-6 flex flex-col gap-5 overflow-y-auto">
        <header className="flex items-center gap-3 mb-2">
          <div className="bg-white p-2 rounded-sm rotate-3">
            <Layers size={22} color="black" />
          </div>
          <div>
            <h1 className="font-black italic text-2xl tracking-tighter uppercase leading-none">CVMNG CONSOLE</h1>
            <span className="text-[10px] text-zinc-600 font-mono tracking-widest uppercase text-xs">Individual X-FX Pro</span>
          </div>
        </header>

        <section>
          <label className="text-[10px] font-black uppercase text-zinc-600 tracking-widest mb-2 block">Box Testo</label>
          <input 
            type="text" 
            value={text} 
            onChange={(e) => setText(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-800 rounded p-3 text-lg font-bold focus:border-white focus:bg-black outline-none transition-all"
          />
        </section>

        <section>
          <label className="text-[10px] font-black uppercase text-zinc-600 tracking-widest mb-2 block">Bulk Font Loader</label>
          <textarea 
            placeholder='Tag <link> di Google Fonts...'
            value={embedCode}
            onChange={(e) => setEmbedCode(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-800 rounded p-3 text-[10px] font-mono h-20 outline-none focus:border-blue-500 mb-2 resize-none"
          />
          <button 
            onClick={handleLoadFonts}
            className="w-full bg-blue-700 hover:bg-blue-600 text-white font-black py-2 rounded-sm text-xs uppercase flex items-center justify-center gap-2 transition-colors"
          >
            <Zap size={14} /> Inietta Collezione
          </button>
        </section>

        <section className="space-y-4 pt-4 border-t border-zinc-900">
          <div className="flex items-center gap-2 mb-1">
            <Sliders size={14} className="text-zinc-500" />
            <span className="text-[10px] font-black uppercase text-zinc-500 tracking-widest text-xs">Master Sidebar</span>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-[9px] uppercase font-bold text-zinc-500 italic">Size: {fontSize}px</label>
              <input type="range" min="20" max="150" value={fontSize} onChange={(e) => setFontSize(parseInt(e.target.value))} className="accent-white h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[9px] uppercase font-bold text-zinc-500 italic">Kern: {letterSpacing}px</label>
              <input type="range" min="-15" max="60" value={letterSpacing} onChange={(e) => setLetterSpacing(parseInt(e.target.value))} className="accent-white h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer" />
            </div>
          </div>

          <div className="flex items-center justify-between bg-zinc-900/50 p-3 rounded border border-zinc-900">
            <label className="text-[10px] uppercase font-bold text-zinc-400">Master Color</label>
            <div className="flex items-center gap-3">
              <button onClick={randomizeAllEverything} className="p-1.5 bg-zinc-800 rounded text-red-500 hover:bg-white hover:text-black transition-all shadow-lg">
                <Shuffle size={14} />
              </button>
              <input type="color" value={globalColor} onChange={(e) => setGlobalColor(e.target.value)} className="w-6 h-6 bg-transparent border-none cursor-pointer scale-125" />
            </div>
          </div>
        </section>

        <section className="space-y-4 pt-4 border-t border-zinc-900">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={14} className="text-red-500" />
            <span className="text-[10px] font-black uppercase text-red-500 tracking-widest text-xs">Master Effects</span>
          </div>

          <div className="grid grid-cols-2 gap-4">
             <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center">
                <label className="text-[9px] uppercase font-bold text-zinc-500 italic">Glow</label>
                <input type="color" value={glowColor} onChange={(e) => setGlowColor(e.target.value)} className="w-4 h-4 bg-transparent cursor-pointer" />
              </div>
              <input type="range" min="0" max="80" value={glowStrength} onChange={(e) => setGlowStrength(parseInt(e.target.value))} className="accent-red-600 h-1 bg-zinc-800 rounded-lg appearance-none" />
            </div>
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center">
                <label className="text-[9px] uppercase font-bold text-zinc-500 italic">Stroke</label>
                <input type="color" value={strokeColor} onChange={(e) => setStrokeColor(e.target.value)} className="w-4 h-4 bg-transparent cursor-pointer" />
              </div>
              <input type="range" min="0" max="20" value={strokeWidth} onChange={(e) => setStrokeWidth(parseInt(e.target.value))} className="accent-blue-600 h-1 bg-zinc-800 rounded-lg appearance-none" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
             <div className="flex flex-col gap-1">
              <label className="text-[9px] uppercase font-bold text-zinc-500 italic">Blur: {blurAmount}px</label>
              <input type="range" min="0" max="20" value={blurAmount} onChange={(e) => setBlurAmount(parseInt(e.target.value))} className="accent-zinc-500 h-1 bg-zinc-800 rounded-lg appearance-none" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[9px] uppercase font-bold text-zinc-500 italic">Skew: {skewAmount}°</label>
              <input type="range" min="-45" max="45" value={skewAmount} onChange={(e) => setSkewAmount(parseInt(e.target.value))} className="accent-zinc-500 h-1 bg-zinc-800 rounded-lg appearance-none" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-2">
            <button onClick={() => setIsGlitch(!isGlitch)} className={`p-2 text-[9px] font-black uppercase rounded-sm border transition-all ${isGlitch ? 'bg-red-600 border-red-600 text-white' : 'border-zinc-800 text-zinc-500 hover:border-zinc-600'}`}>Glitch</button>
            <button onClick={() => setIs3D(!is3D)} className={`p-2 text-[9px] font-black uppercase rounded-sm border transition-all ${is3D ? 'bg-blue-600 border-blue-600 text-white' : 'border-zinc-800 text-zinc-500 hover:border-zinc-600'}`}>Depth 3D</button>
            <button onClick={() => setHasReflection(!hasReflection)} className={`p-2 text-[9px] font-black uppercase rounded-sm border transition-all ${hasReflection ? 'bg-green-600 border-green-600 text-white' : 'border-zinc-800 text-zinc-500 hover:border-zinc-600'}`}>Mirror</button>
          </div>
        </section>

        <div className="mt-auto pt-6 border-t border-zinc-900">
           <div className="flex items-center justify-between mb-3">
             <label className="text-[10px] font-black uppercase text-zinc-600 tracking-widest text-xs">Stack Attivo ({loadedFonts.length})</label>
             <button onClick={() => setLoadedFonts([{ name: 'sans-serif', id: 'default', customColor: null, customGlow: null, customGlowColor: null, customStroke: null, customStrokeColor: null, customBlur: null, customSkew: null, customFontSize: null, customLetterSpacing: null }])} className="text-[9px] text-red-500 hover:underline uppercase font-bold">Resetta</button>
           </div>
           <div className="flex flex-wrap gap-2 max-h-[120px] overflow-y-auto pr-2 custom-scrollbar">
             {loadedFonts.map(f => (
               <div key={f.id} className="flex items-center gap-2 bg-zinc-900 px-2 py-1 rounded-sm text-[9px] font-bold border border-zinc-800">
                 <span style={{ color: f.customColor || globalColor }}>{f.name}</span>
                 {f.id !== 'default' && (
                   <button onClick={() => removeFont(f.id)} className="text-zinc-600 hover:text-red-500"><Trash2 size={10} /></button>
                 )}
               </div>
             ))}
           </div>
        </div>
      </aside>

      {/* --- Main Content Gallery --- */}
      <main className="flex-1 overflow-y-auto bg-zinc-950 relative">
        <div className="sticky top-0 z-30 bg-zinc-950/90 backdrop-blur-xl p-4 border-b border-zinc-900 flex justify-between items-center">
          <div className="flex items-center gap-3 text-xs font-mono text-zinc-500 uppercase tracking-widest">
            <Grid size={14} />
            Galleria di Rendering
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={handleDownloadAll}
              disabled={isDownloadingAll}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-sm font-black text-[10px] transition-all uppercase ${isDownloadingAll ? 'bg-zinc-800 text-zinc-500' : 'bg-white text-black hover:bg-green-500 hover:text-white'}`}
            >
              {isDownloadingAll ? <><Loader2 size={12} className="animate-spin" /> {downloadProgress}%</> : <><Archive size={12} /> Scarica Batch</>}
            </button>
            <button 
              onClick={randomizeAllEverything}
              className="flex items-center gap-2 bg-red-600 text-white px-4 py-1.5 rounded-sm font-black text-[10px] hover:bg-white hover:text-red-600 transition-all uppercase"
            >
              <Shuffle size={12} /> Chaos All
            </button>
          </div>
        </div>

        <div className="p-8 grid grid-cols-1 gap-12 max-w-6xl mx-auto">
          {loadedFonts.map((font) => {
            const activeColor = font.customColor || globalColor;
            const activeGlow = font.customGlow !== null ? font.customGlow : glowStrength;
            const activeGlowColor = font.customGlowColor || glowColor;
            const activeStroke = font.customStroke !== null ? font.customStroke : strokeWidth;
            const activeStrokeColor = font.customStrokeColor || strokeColor;
            const activeFontSize = font.customFontSize !== null ? font.customFontSize : fontSize;
            const activeSpacing = font.customLetterSpacing !== null ? font.customLetterSpacing : letterSpacing;
            const activeBlur = font.customBlur !== null ? font.customBlur : blurAmount;
            const activeSkew = font.customSkew !== null ? font.customSkew : skewAmount;

            return (
              <div key={font.id} className="group relative bg-zinc-900/10 border border-zinc-900/50 rounded-2xl p-16 hover:bg-zinc-900/20 hover:border-zinc-800 transition-all overflow-hidden">
                {/* Card Controls (Toolbar) */}
                <div className="absolute top-4 right-4 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all translate-y-2 group-hover:translate-y-0 z-20">
                  <div className="flex bg-black p-1 rounded-sm border border-zinc-800 shadow-2xl">
                    <button onClick={() => setEditingId(font.id)} className="p-1.5 hover:text-blue-400 transition-colors" title="Modifica X-FX Individualmente">
                      <Settings2 size={14} />
                    </button>
                    <button onClick={() => randomizeSingleEverything(font.id)} className="p-1.5 hover:text-red-500 transition-colors border-l border-zinc-800 ml-1 pl-2" title="Randomize X-FX">
                      <Zap size={14} />
                    </button>
                  </div>
                  <span className="text-[10px] font-mono text-zinc-500 bg-black px-3 py-1.5 rounded-sm border border-zinc-800 uppercase tracking-tighter">
                    {font.name}
                  </span>
                  <button onClick={() => downloadFontImage(font)} className="bg-white text-black p-2.5 rounded-sm hover:bg-red-600 hover:text-white transition-all shadow-xl active:scale-95">
                    <Download size={16} />
                  </button>
                </div>

                {/* Rendering Area */}
                <div className="flex flex-col items-center justify-center min-h-[160px] relative">
                  {hasReflection && (
                    <div className="absolute top-[100%] scale-y-[-0.6] opacity-20 blur-[1px] select-none pointer-events-none origin-top"
                         style={{
                           fontFamily: `"${font.name}", sans-serif`, fontSize: `${activeFontSize}px`, color: activeColor, letterSpacing: `${activeSpacing}px`, transform: `scaleY(-0.6) skew(${activeSkew}deg)`, maskImage: 'linear-gradient(to bottom, black, transparent)'
                         }}>{text}</div>
                  )}
                  {isGlitch && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="absolute text-red-500 mix-blend-screen animate-pulse opacity-40 whitespace-nowrap"
                        style={{ fontFamily: `"${font.name}", sans-serif`, fontSize: `${activeFontSize}px`, letterSpacing: `${activeSpacing}px`, transform: `skew(${activeSkew}deg) translateX(-6px)`, filter: `blur(${activeBlur}px)` }}>{text}</div>
                      <div className="absolute text-cyan-400 mix-blend-screen animate-bounce opacity-40 whitespace-nowrap"
                        style={{ fontFamily: `"${font.name}", sans-serif`, fontSize: `${activeFontSize}px`, letterSpacing: `${activeSpacing}px`, transform: `skew(${activeSkew}deg) translateX(6px)`, filter: `blur(${activeBlur}px)` }}>{text}</div>
                    </div>
                  )}
                  <div className="relative whitespace-nowrap transition-all duration-300 select-all"
                    style={{
                      fontFamily: `"${font.name}", sans-serif`, fontSize: `${activeFontSize}px`, color: activeColor, letterSpacing: `${activeSpacing}px`, transform: `skew(${activeSkew}deg)`, WebkitTextStroke: activeStroke > 0 ? `${activeStroke}px ${activeStrokeColor}` : 'none', filter: `${activeBlur > 0 ? `blur(${activeBlur}px)` : ''}${isGlitch ? 'hue-rotate(90deg) contrast(1.1)' : ''}`, textShadow: `${activeGlow > 0 ? `0 0 ${activeGlow}px ${activeGlowColor}, 0 0 ${activeGlow/2}px ${activeGlowColor}` : '0 0 0 transparent'},${is3D ? `1px 1px 0px rgba(0,0,0,0.9),2px 2px 0px rgba(0,0,0,0.8),3px 3px 0px rgba(0,0,0,0.7),4px 4px 0px rgba(0,0,0,0.6),5px 5px 0px rgba(0,0,0,0.5),6px 6px 0px rgba(0,0,0,0.4),8px 8px 15px rgba(0,0,0,0.5)` : '0 0 0 transparent'}`,
                    }}>{text}</div>
                </div>
              </div>
            );
          })}
        </div>

        {/* --- GLOBAL OVERLAY EDITOR (LARGE POPUP) --- */}
        {editingId && editingFont && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-10 bg-black/90 backdrop-blur-xl animate-in fade-in duration-300">
            <div className="bg-zinc-950 border border-zinc-800 w-full max-w-7xl h-full max-h-[90vh] rounded-3xl overflow-hidden flex flex-col shadow-[0_0_100px_rgba(0,0,0,1)] relative">
              
              {/* Header */}
              <div className="p-6 border-b border-zinc-900 flex justify-between items-center bg-zinc-900/50">
                <div className="flex items-center gap-4">
                  <div className="bg-blue-600 p-2 rounded-lg">
                    <Settings2 size={24} color="white" />
                  </div>
                  <div>
                    <h2 className="font-black text-xl uppercase tracking-widest leading-none">Editor Individuale</h2>
                    <span className="text-xs text-zinc-500 font-mono italic">Stai modificando: {editingFont.name}</span>
                  </div>
                </div>
                <button 
                  onClick={() => setEditingId(null)}
                  className="p-3 hover:bg-red-600 hover:text-white rounded-full transition-all bg-zinc-800"
                >
                  <X size={24} />
                </button>
              </div>

              {/* Main Workspace */}
              <div className="flex-1 flex flex-col overflow-hidden">
                
                {/* PREVIEW AREA (DOMINANT TOP) */}
                <div className="h-2/5 min-h-[300px] border-b border-zinc-900 bg-[radial-gradient(#27272a_1px,transparent_1px)] [background-size:24px_24px] flex items-center justify-center relative group">
                   <div className="absolute top-4 left-6 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-zinc-600">
                     <Sparkles size={12} /> Live Preview Rendering
                   </div>
                   
                   <div className="relative">
                      {hasReflection && (
                        <div className="absolute top-[100%] scale-y-[-0.6] opacity-20 blur-[2px] select-none pointer-events-none origin-top"
                             style={{
                               fontFamily: `"${editingFont.name}", sans-serif`,
                               fontSize: `${editingFont.customFontSize || fontSize}px`,
                               color: editingFont.customColor || globalColor,
                               letterSpacing: `${editingFont.customLetterSpacing || letterSpacing}px`,
                               transform: `scaleY(-0.6) skew(${editingFont.customSkew || skewAmount}deg)`,
                               maskImage: 'linear-gradient(to bottom, black, transparent)'
                             }}>{text}</div>
                      )}
                      {isGlitch && (
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                          <div className="absolute text-red-500 mix-blend-screen animate-pulse opacity-40 whitespace-nowrap"
                            style={{ fontFamily: `"${editingFont.name}", sans-serif`, fontSize: `${editingFont.customFontSize || fontSize}px`, letterSpacing: `${editingFont.customLetterSpacing || letterSpacing}px`, transform: `skew(${editingFont.customSkew || skewAmount}deg) translateX(-6px)`, filter: `blur(${editingFont.customBlur || blurAmount}px)` }}>{text}</div>
                          <div className="absolute text-cyan-400 mix-blend-screen animate-bounce opacity-40 whitespace-nowrap"
                            style={{ fontFamily: `"${editingFont.name}", sans-serif`, fontSize: `${editingFont.customFontSize || fontSize}px`, letterSpacing: `${editingFont.customLetterSpacing || letterSpacing}px`, transform: `skew(${editingFont.customSkew || skewAmount}deg) translateX(6px)`, filter: `blur(${editingFont.customBlur || blurAmount}px)` }}>{text}</div>
                        </div>
                      )}
                      <div className="relative whitespace-nowrap transition-all duration-300"
                        style={{
                          fontFamily: `"${editingFont.name}", sans-serif`,
                          fontSize: `${editingFont.customFontSize || fontSize}px`,
                          color: editingFont.customColor || globalColor,
                          letterSpacing: `${editingFont.customLetterSpacing || letterSpacing}px`,
                          transform: `skew(${editingFont.customSkew || skewAmount}deg)`,
                          WebkitTextStroke: (editingFont.customStroke !== null ? editingFont.customStroke : strokeWidth) > 0 ? `${editingFont.customStroke !== null ? editingFont.customStroke : strokeWidth}px ${editingFont.customStrokeColor || strokeColor}` : 'none',
                          filter: `${(editingFont.customBlur !== null ? editingFont.customBlur : blurAmount) > 0 ? `blur(${editingFont.customBlur !== null ? editingFont.customBlur : blurAmount}px)` : ''}${isGlitch ? 'hue-rotate(90deg) contrast(1.1)' : ''}`,
                          textShadow: `${(editingFont.customGlow !== null ? editingFont.customGlow : glowStrength) > 0 ? `0 0 ${editingFont.customGlow !== null ? editingFont.customGlow : glowStrength}px ${editingFont.customGlowColor || glowColor}, 0 0 ${(editingFont.customGlow !== null ? editingFont.customGlow : glowStrength)/2}px ${editingFont.customGlowColor || glowColor}` : '0 0 0 transparent'},${is3D ? `1px 1px 0px rgba(0,0,0,0.9),2px 2px 0px rgba(0,0,0,0.8),3px 3px 0px rgba(0,0,0,0.7),4px 4px 0px rgba(0,0,0,0.6),5px 5px 0px rgba(0,0,0,0.5),6px 6px 0px rgba(0,0,0,0.4),8px 8px 15px rgba(0,0,0,0.5)` : '0 0 0 transparent'}`,
                        }}>{text}</div>
                   </div>
                </div>

                {/* CONTROLS AREA (BOTTOM SCROLLABLE) */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar bg-zinc-950">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-10 max-w-6xl mx-auto">
                    
                    {/* Col 1: Colors */}
                    <div className="space-y-6">
                      <h3 className="text-[10px] font-black uppercase text-zinc-500 tracking-[0.3em] flex items-center gap-2">
                        <Palette size={14} /> Colorazione Card
                      </h3>
                      <div className="grid gap-4">
                        <div className="flex items-center justify-between bg-zinc-900/50 p-4 rounded-xl border border-zinc-900">
                          <span className="text-xs font-bold uppercase italic">Testo Principale</span>
                          <input type="color" value={editingFont.customColor || globalColor} onChange={(e) => updateIndividualParam(editingId, 'customColor', e.target.value)} className="w-10 h-10 bg-transparent cursor-pointer" />
                        </div>
                        <div className="flex items-center justify-between bg-zinc-900/50 p-4 rounded-xl border border-zinc-900">
                          <span className="text-xs font-bold uppercase italic text-red-500">Colore Bagliore</span>
                          <input type="color" value={editingFont.customGlowColor || glowColor} onChange={(e) => updateIndividualParam(editingId, 'customGlowColor', e.target.value)} className="w-10 h-10 bg-transparent cursor-pointer" />
                        </div>
                        <div className="flex items-center justify-between bg-zinc-900/50 p-4 rounded-xl border border-zinc-900">
                          <span className="text-xs font-bold uppercase italic text-blue-500">Colore Contorno</span>
                          <input type="color" value={editingFont.customStrokeColor || strokeColor} onChange={(e) => updateIndividualParam(editingId, 'customStrokeColor', e.target.value)} className="w-10 h-10 bg-transparent cursor-pointer" />
                        </div>
                      </div>
                    </div>

                    {/* Col 2: FX Parameters */}
                    <div className="space-y-6">
                      <h3 className="text-[10px] font-black uppercase text-zinc-500 tracking-[0.3em] flex items-center gap-2">
                        <Zap size={14} /> Intensità Effetti
                      </h3>
                      <div className="space-y-6 bg-zinc-900/30 p-6 rounded-2xl border border-zinc-900">
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-[10px] font-bold uppercase">Glow Strength: {editingFont.customGlow !== null ? editingFont.customGlow : glowStrength}</span>
                            {editingFont.customGlow !== null && <button onClick={() => updateIndividualParam(editingId, 'customGlow', null)} className="text-[8px] text-red-500 font-black">RESET</button>}
                          </div>
                          <input type="range" min="0" max="100" value={editingFont.customGlow !== null ? editingFont.customGlow : glowStrength} onChange={(e) => updateIndividualParam(editingId, 'customGlow', parseInt(e.target.value))} className="w-full h-1.5 bg-zinc-800 accent-red-600 rounded-lg appearance-none cursor-pointer" />
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-[10px] font-bold uppercase">Stroke Width: {editingFont.customStroke !== null ? editingFont.customStroke : strokeWidth}</span>
                            {editingFont.customStroke !== null && <button onClick={() => updateIndividualParam(editingId, 'customStroke', null)} className="text-[8px] text-red-500 font-black">RESET</button>}
                          </div>
                          <input type="range" min="0" max="25" value={editingFont.customStroke !== null ? editingFont.customStroke : strokeWidth} onChange={(e) => updateIndividualParam(editingId, 'customStroke', parseInt(e.target.value))} className="w-full h-1.5 bg-zinc-800 accent-blue-600 rounded-lg appearance-none cursor-pointer" />
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-[10px] font-bold uppercase">Blur Effect: {editingFont.customBlur !== null ? editingFont.customBlur : blurAmount}</span>
                            {editingFont.customBlur !== null && <button onClick={() => updateIndividualParam(editingId, 'customBlur', null)} className="text-[8px] text-red-500 font-black">RESET</button>}
                          </div>
                          <input type="range" min="0" max="30" value={editingFont.customBlur !== null ? editingFont.customBlur : blurAmount} onChange={(e) => updateIndividualParam(editingId, 'customBlur', parseInt(e.target.value))} className="w-full h-1.5 bg-zinc-800 accent-zinc-500 rounded-lg appearance-none cursor-pointer" />
                        </div>
                      </div>
                    </div>

                    {/* Col 3: Layout Parameters */}
                    <div className="space-y-6">
                      <h3 className="text-[10px] font-black uppercase text-zinc-500 tracking-[0.3em] flex items-center gap-2">
                        <Type size={14} /> Geometria Font
                      </h3>
                      <div className="space-y-6 bg-zinc-900/30 p-6 rounded-2xl border border-zinc-900">
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-[10px] font-bold uppercase">Font Size: {editingFont.customFontSize || fontSize}px</span>
                            {editingFont.customFontSize !== null && <button onClick={() => updateIndividualParam(editingId, 'customFontSize', null)} className="text-[8px] text-red-500 font-black">RESET</button>}
                          </div>
                          <input type="range" min="20" max="300" value={editingFont.customFontSize || fontSize} onChange={(e) => updateIndividualParam(editingId, 'customFontSize', parseInt(e.target.value))} className="w-full h-1.5 bg-zinc-800 accent-white rounded-lg appearance-none cursor-pointer" />
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-[10px] font-bold uppercase">Letter Spacing: {editingFont.customLetterSpacing || letterSpacing}px</span>
                            {editingFont.customLetterSpacing !== null && <button onClick={() => updateIndividualParam(editingId, 'customLetterSpacing', null)} className="text-[8px] text-red-500 font-black">RESET</button>}
                          </div>
                          <input type="range" min="-20" max="100" value={editingFont.customLetterSpacing || letterSpacing} onChange={(e) => updateIndividualParam(editingId, 'customLetterSpacing', parseInt(e.target.value))} className="w-full h-1.5 bg-zinc-800 accent-white rounded-lg appearance-none cursor-pointer" />
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-[10px] font-bold uppercase">Skew Distortion: {editingFont.customSkew || skewAmount}°</span>
                            {editingFont.customSkew !== null && <button onClick={() => updateIndividualParam(editingId, 'customSkew', null)} className="text-[8px] text-red-500 font-black">RESET</button>}
                          </div>
                          <input type="range" min="-60" max="60" value={editingFont.customSkew || skewAmount} onChange={(e) => updateIndividualParam(editingId, 'customSkew', parseInt(e.target.value))} className="w-full h-1.5 bg-zinc-800 accent-zinc-500 rounded-lg appearance-none cursor-pointer" />
                        </div>
                      </div>
                    </div>

                  </div>
                </div>
              </div>

              {/* Footer Actions */}
              <div className="p-6 border-t border-zinc-900 flex justify-between items-center bg-zinc-900/30">
                <button 
                  onClick={() => resetSingleEverything(editingId)}
                  className="flex items-center gap-2 px-6 py-3 border border-zinc-800 rounded-xl hover:bg-zinc-800 transition-all font-black text-xs uppercase"
                >
                  <RotateCcw size={16} /> Reset Totale Font
                </button>
                <div className="flex gap-4">
                  <button 
                    onClick={() => downloadFontImage(editingFont)}
                    className="flex items-center gap-2 px-6 py-3 border border-blue-600 text-blue-400 rounded-xl hover:bg-blue-600 hover:text-white transition-all font-black text-xs uppercase"
                  >
                    <Download size={16} /> Scarica Singolo PNG
                  </button>
                  <button 
                    onClick={() => setEditingId(null)}
                    className="flex items-center gap-2 px-10 py-3 bg-white text-black rounded-xl hover:bg-green-500 hover:text-white transition-all font-black text-xs uppercase shadow-2xl"
                  >
                    Salva & Chiudi
                  </button>
                </div>
              </div>

            </div>
          </div>
        )}

        {loadedFonts.length === 1 && (
           <div className="flex flex-col items-center justify-center p-32 text-zinc-800">
             <Box size={64} strokeWidth={1} className="mb-6 opacity-10 animate-spin-slow" />
             <p className="text-xs font-black uppercase tracking-[0.4em] opacity-20 text-center leading-relaxed">Incolla i font Google <br/> nell'header per iniziare</p>
           </div>
        )}
      </main>
    </div>
  );
};

export default App;