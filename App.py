"""
DeepFace — Análisis Facial en Tiempo Real
Cámara web del navegador · Análisis cada 4 segundos
"""

from flask import Flask, request, jsonify, render_template_string
from analyzer import analyze_from_bytes
import base64, os

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DeepFace — Tiempo Real</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg:          #0a0c10;
      --surface:     #111318;
      --surface-2:   #1a1d24;
      --border:      #252830;
      --accent:      #6ee7f7;
      --accent-dim:  #1a3d44;
      --accent-2:    #a78bfa;
      --accent-2-dim:#2a1f44;
      --text:        #e8eaf0;
      --text-muted:  #6b7280;
      --success:     #34d399;
      --danger:      #f87171;
      --radius:      12px;
      --radius-sm:   8px;
      --font-mono:   'Space Mono', monospace;
      --font-body:   'Space Grotesk', sans-serif;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-body);
      font-size: 15px;
      line-height: 1.6;
      min-height: 100vh;
      overflow-x: hidden;
    }

    body::before {
      content: '';
      position: fixed; inset: 0;
      background-image:
        linear-gradient(rgba(110,231,247,.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(110,231,247,.03) 1px, transparent 1px);
      background-size: 40px 40px;
      pointer-events: none; z-index: 0;
    }

    .app {
      position: relative; z-index: 1;
      max-width: 1000px;
      margin: 0 auto;
      padding: 2rem 1.25rem 4rem;
    }

    /* ── HEADER ── */
    header { text-align: center; padding: 2.5rem 0 2rem; }

    .logo-badge {
      display: inline-flex; align-items: center; gap: .5rem;
      background: var(--accent-dim); border: 1px solid var(--accent);
      color: var(--accent); font-family: var(--font-mono);
      font-size: .7rem; letter-spacing: .12em;
      padding: .35rem .75rem; border-radius: 999px; margin-bottom: 1.2rem;
    }
    .logo-badge::before {
      content: ''; width: 6px; height: 6px; border-radius: 50%;
      background: var(--accent); animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
      0%,100% { opacity:1; transform:scale(1); }
      50%      { opacity:.4; transform:scale(.7); }
    }

    h1 {
      font-family: var(--font-mono);
      font-size: clamp(1.5rem, 3.5vw, 2.2rem);
      font-weight: 700; letter-spacing: -.02em; margin-bottom: .5rem;
    }
    h1 span { color: var(--accent); text-shadow: 0 0 30px rgba(110,231,247,.4); }
    .subtitle { color: var(--text-muted); font-size: .88rem; letter-spacing: .04em; }

    /* ── TABS ── */
    .tabs {
      display: flex; gap: .5rem;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: .35rem;
      margin-bottom: 1.5rem;
    }
    .tab-btn {
      flex: 1; padding: .6rem 1rem;
      background: transparent; border: none;
      border-radius: var(--radius-sm);
      color: var(--text-muted); font-family: var(--font-mono);
      font-size: .75rem; letter-spacing: .08em;
      cursor: pointer; transition: background .2s, color .2s;
    }
    .tab-btn.active {
      background: var(--accent-dim);
      color: var(--accent);
    }

    /* ── MAIN GRID ── */
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.25rem;
      align-items: start;
    }
    @media (max-width: 680px) { .main-grid { grid-template-columns: 1fr; } }

    /* ── VIDEO PANEL ── */
    .video-panel {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
    }

    .panel-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: .75rem 1rem;
      background: var(--surface-2);
      border-bottom: 1px solid var(--border);
    }
    .panel-title {
      font-family: var(--font-mono); font-size: .7rem;
      letter-spacing: .1em; color: var(--text-muted);
    }

    /* Indicador LIVE */
    .live-dot {
      display: flex; align-items: center; gap: .4rem;
      font-family: var(--font-mono); font-size: .65rem;
      letter-spacing: .1em;
    }
    .live-dot .dot {
      width: 7px; height: 7px; border-radius: 50%;
      background: var(--text-muted);
      transition: background .3s;
    }
    .live-dot.active .dot { background: var(--success); animation: pulse 1.5s infinite; }
    .live-dot.active { color: var(--success); }

    /* Video */
    .video-wrapper { position: relative; aspect-ratio: 4/3; background: #000; }
    #webcam {
      width: 100%; height: 100%;
      object-fit: cover; display: block;
      transform: scaleX(-1); /* espejo */
    }
    #canvas { display: none; }

    /* Overlay de cuenta regresiva */
    .countdown-overlay {
      position: absolute; bottom: .75rem; right: .75rem;
      background: rgba(0,0,0,.65); backdrop-filter: blur(4px);
      border: 1px solid var(--border);
      border-radius: 8px; padding: .3rem .65rem;
      font-family: var(--font-mono); font-size: .75rem;
      color: var(--text-muted);
      display: none;
    }
    .countdown-overlay span { color: var(--accent); }

    /* Overlay de status */
    .status-overlay {
      position: absolute; inset: 0;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      background: rgba(10,12,16,.85);
      gap: .75rem;
    }
    .status-icon { font-size: 2.5rem; }
    .status-text {
      font-family: var(--font-mono); font-size: .8rem;
      color: var(--text-muted); letter-spacing: .08em;
      text-align: center;
    }

    /* Barra de progreso del análisis */
    .progress-bar {
      position: absolute; bottom: 0; left: 0;
      height: 3px; background: var(--accent);
      width: 0%; transition: width linear;
      box-shadow: 0 0 8px var(--accent);
    }

    /* ── CONTROLES ── */
    .controls {
      display: flex; gap: .6rem;
      padding: .75rem 1rem;
    }

    .btn {
      flex: 1; padding: .65rem;
      border: 1px solid var(--border); border-radius: var(--radius-sm);
      font-family: var(--font-mono); font-size: .75rem;
      letter-spacing: .06em; cursor: pointer;
      transition: all .2s;
    }
    .btn-primary {
      background: var(--accent); color: #000; border-color: var(--accent);
    }
    .btn-primary:hover { box-shadow: 0 0 20px rgba(110,231,247,.35); }
    .btn-secondary {
      background: transparent; color: var(--text-muted);
    }
    .btn-secondary:hover { border-color: var(--danger); color: var(--danger); }
    .btn:disabled { opacity: .3; cursor: not-allowed; }

    /* ── PANEL RESULTADOS ── */
    .results-panel {
      display: flex; flex-direction: column; gap: 1rem;
    }

    /* Estado vacío */
    .empty-state {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 2rem 1.5rem;
      text-align: center;
    }
    .empty-state .icon { font-size: 2rem; margin-bottom: .75rem; }
    .empty-state p { color: var(--text-muted); font-size: .85rem; }

    /* Timestamp */
    .result-timestamp {
      font-family: var(--font-mono); font-size: .65rem;
      color: var(--text-muted); letter-spacing: .08em;
      padding: .5rem 0 .25rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: .75rem;
    }

    /* Face card */
    .face-card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); overflow: hidden;
      animation: slideUp .35s ease both;
    }
    @keyframes slideUp {
      from { opacity:0; transform:translateY(12px); }
      to   { opacity:1; transform:translateY(0); }
    }

    .face-card-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: .7rem 1rem;
      background: var(--surface-2); border-bottom: 1px solid var(--border);
    }
    .face-number { font-family: var(--font-mono); font-size: .7rem; color: var(--accent); }

    .face-card-body {
      display: grid; grid-template-columns: repeat(3, 1fr);
    }
    .stat-cell {
      padding: .85rem 1rem;
      border-right: 1px solid var(--border);
    }
    .stat-cell:last-child { border-right: none; }
    .stat-label {
      font-size: .68rem; color: var(--text-muted);
      letter-spacing: .06em; text-transform: uppercase; margin-bottom: .3rem;
    }
    .stat-value { font-family: var(--font-mono); font-size: 1rem; font-weight: 700; }
    .stat-sub   { font-size: .72rem; color: var(--text-muted); margin-top: .15rem; }

    /* Emociones */
    .emotions-section { padding: .85rem 1rem; border-top: 1px solid var(--border); }
    .emotions-title {
      font-size: .68rem; color: var(--text-muted);
      letter-spacing: .06em; text-transform: uppercase; margin-bottom: .6rem;
    }
    .emotion-row { display: flex; align-items: center; gap: .5rem; margin-bottom: .4rem; }
    .emotion-name { font-size: .75rem; width: 76px; flex-shrink: 0; }
    .bar-track { flex:1; height:5px; background:var(--surface-2); border-radius:999px; overflow:hidden; }
    .bar-fill {
      height:100%; border-radius:999px;
      background: var(--accent-2);
      transition: width .8s cubic-bezier(.16,1,.3,1);
    }
    .bar-fill.top { background: var(--accent); }
    .emotion-pct { font-family: var(--font-mono); font-size: .68rem; color: var(--text-muted); width:34px; text-align:right; }

    /* Error */
    .error-box {
      background: rgba(248,113,113,.08); border: 1px solid rgba(248,113,113,.3);
      color: var(--danger); border-radius: var(--radius-sm);
      padding: .85rem 1rem; font-size: .83rem;
    }

    /* ── TABS VISIBILIDAD ── */
    #tab-camera { display: block; }
    #tab-image  { display: none;  }

    .upload-zone {
      border: 2px dashed var(--border); border-radius: var(--radius);
      padding: 2.5rem 2rem; text-align: center; cursor: pointer;
      transition: border-color .25s, background .25s;
      position: relative; margin-bottom: 1.25rem;
    }
    .upload-zone:hover { border-color: var(--accent); background: rgba(110,231,247,.03); }
    .upload-zone input { position:absolute; inset:0; opacity:0; cursor:pointer; width:100%; height:100%; }
    .upload-icon {
      width:48px; height:48px; margin:0 auto .85rem;
      background:var(--accent-dim); border-radius:50%;
      display:flex; align-items:center; justify-content:center; font-size:1.3rem;
    }
    .upload-title { font-weight:600; margin-bottom:.3rem; }
    .upload-hint  { color:var(--text-muted); font-size:.8rem; }

    #preview-container {
      display:none; margin-bottom:1.25rem;
      border-radius:var(--radius); overflow:hidden;
      border:1px solid var(--border);
    }
    #preview-container img { width:100%; display:block; max-height:300px; object-fit:cover; }

    .btn-full {
      width:100%; padding:.85rem;
      background:var(--accent); color:#000; border:none;
      border-radius:var(--radius-sm);
      font-family:var(--font-mono); font-size:.82rem;
      font-weight:700; letter-spacing:.06em;
      cursor:pointer; transition:all .2s; margin-bottom:1.5rem;
    }
    .btn-full:hover:not(:disabled) { box-shadow:0 0 24px rgba(110,231,247,.35); }
    .btn-full:disabled { opacity:.3; cursor:not-allowed; }

    .spinner {
      display:inline-block; width:13px; height:13px;
      border:2px solid rgba(0,0,0,.3); border-top-color:#000;
      border-radius:50%; animation:spin .7s linear infinite;
      vertical-align:middle; margin-right:.4rem;
    }
    @keyframes spin { to { transform:rotate(360deg); } }

    #annotated-container {
      display:none; border-radius:var(--radius); overflow:hidden;
      border:1px solid var(--border); margin-bottom:1.25rem;
    }
    #annotated-container img { width:100%; display:block; }

    footer {
      text-align:center; margin-top:4rem;
      color:var(--text-muted); font-size:.75rem;
      font-family:var(--font-mono); letter-spacing:.04em;
    }

    @media (prefers-reduced-motion: reduce) {
      *, .bar-fill, .face-card, .progress-bar { animation:none!important; transition:none!important; }
    }
  </style>
</head>
<body>
<div class="app">

  <header>
    <div class="logo-badge">DEEPFACE · ANÁLISIS FACIAL</div>
    <h1>Rostros bajo la <span>lupa</span></h1>
    <p class="subtitle">Tiempo real · Género · Edad · Emoción · Etnia</p>
  </header>

  <!-- Tabs -->
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('camera')">📷 CÁMARA EN VIVO</button>
    <button class="tab-btn"        onclick="switchTab('image')">🖼 SUBIR IMAGEN</button>
  </div>

  <!-- ═══════════ TAB CÁMARA ═══════════ -->
  <div id="tab-camera">
    <div class="main-grid">

      <!-- Panel video -->
      <div class="video-panel">
        <div class="panel-header">
          <span class="panel-title">CÁMARA WEB</span>
          <span class="live-dot" id="live-dot">
            <span class="dot"></span> EN ESPERA
          </span>
        </div>

        <div class="video-wrapper">
          <video id="webcam" autoplay playsinline muted></video>
          <canvas id="canvas"></canvas>

          <!-- Overlay inicial -->
          <div class="status-overlay" id="status-overlay">
            <div class="status-icon">📷</div>
            <div class="status-text">Presiona INICIAR<br>para activar la cámara</div>
          </div>

          <!-- Cuenta regresiva -->
          <div class="countdown-overlay" id="countdown-overlay">
            próximo análisis en <span id="countdown-num">4</span>s
          </div>

          <!-- Barra de progreso -->
          <div class="progress-bar" id="progress-bar"></div>
        </div>

        <div class="controls">
          <button class="btn btn-primary" id="start-btn" onclick="startCamera()">INICIAR</button>
          <button class="btn btn-secondary" id="stop-btn" onclick="stopCamera()" disabled>DETENER</button>
        </div>
      </div>

      <!-- Panel resultados -->
      <div class="results-panel" id="results-panel">
        <div class="empty-state">
          <div class="icon">🔍</div>
          <p>Los resultados aparecerán<br>aquí al iniciar la cámara</p>
        </div>
      </div>

    </div>
  </div>

  <!-- ═══════════ TAB IMAGEN ═══════════ -->
  <div id="tab-image">
    <div class="upload-zone" id="upload-zone">
      <input type="file" id="file-input" accept="image/*">
      <div class="upload-icon">📁</div>
      <p class="upload-title">Arrastra una foto o haz clic</p>
      <p class="upload-hint">JPG, PNG, WEBP · máx. 16 MB</p>
    </div>

    <div id="preview-container">
      <img id="preview-img" src="" alt="Vista previa">
    </div>

    <button class="btn-full" id="analyze-btn" disabled>ANALIZAR IMAGEN</button>

    <div id="img-error" class="error-box" style="display:none"></div>
    <div id="annotated-container"><img id="annotated-img" src="" alt=""></div>
    <div id="img-faces"></div>
  </div>

  <footer>Desarrollado con DeepFace · Flask · OpenCV</footer>
</div>

<script>
// ═══════════════════════════════════════
//  TABS
// ═══════════════════════════════════════
function switchTab(tab) {
  document.querySelectorAll('.tab-btn').forEach((b,i) =>
    b.classList.toggle('active', (tab==='camera'&&i===0)||(tab==='image'&&i===1))
  );
  document.getElementById('tab-camera').style.display = tab==='camera' ? 'block' : 'none';
  document.getElementById('tab-image').style.display  = tab==='image'  ? 'block' : 'none';
  if (tab === 'image' && stream) stopCamera();
}

// ═══════════════════════════════════════
//  CÁMARA EN TIEMPO REAL
// ═══════════════════════════════════════
let stream        = null;
let intervalId    = null;
let countdownId   = null;
let isAnalyzing   = false;
const INTERVAL_MS = 4000;   // cada 4 segundos

const webcam       = document.getElementById('webcam');
const canvas       = document.getElementById('canvas');
const ctx          = canvas.getContext('2d');
const startBtn     = document.getElementById('start-btn');
const stopBtn      = document.getElementById('stop-btn');
const liveDot      = document.getElementById('live-dot');
const statusOvl    = document.getElementById('status-overlay');
const countdownOvl = document.getElementById('countdown-overlay');
const countdownNum = document.getElementById('countdown-num');
const progressBar  = document.getElementById('progress-bar');
const resultsPanel = document.getElementById('results-panel');

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    webcam.srcObject = stream;
    startBtn.disabled = true;
    stopBtn.disabled  = false;
    statusOvl.style.display  = 'none';
    countdownOvl.style.display = 'block';

    liveDot.className = 'live-dot active';
    liveDot.innerHTML = '<span class="dot"></span> EN VIVO';

    // Primer análisis inmediato, luego cada 4s
    await captureAndAnalyze();
    scheduleNext();
  } catch (err) {
    showCameraError('No se pudo acceder a la cámara: ' + err.message);
  }
}

function scheduleNext() {
  let remaining = INTERVAL_MS / 1000;
  countdownNum.textContent = remaining;

  // Barra de progreso
  progressBar.style.transition = 'none';
  progressBar.style.width = '0%';
  requestAnimationFrame(() => {
    progressBar.style.transition = `width ${INTERVAL_MS}ms linear`;
    progressBar.style.width = '100%';
  });

  // Cuenta regresiva
  countdownId = setInterval(() => {
    remaining -= 1;
    countdownNum.textContent = Math.max(remaining, 0);
  }, 1000);

  intervalId = setTimeout(async () => {
    clearInterval(countdownId);
    await captureAndAnalyze();
    if (stream) scheduleNext();
  }, INTERVAL_MS);
}

async function captureAndAnalyze() {
  if (isAnalyzing || !stream) return;
  isAnalyzing = true;

  // Capturar frame
  canvas.width  = webcam.videoWidth  || 640;
  canvas.height = webcam.videoHeight || 480;
  ctx.drawImage(webcam, 0, 0);

  canvas.toBlob(async (blob) => {
    try {
      const fd = new FormData();
      fd.append('image', blob, 'frame.jpg');
      const resp = await fetch('/analyze', { method: 'POST', body: fd });
      const data = await resp.json();

      if (data.error) {
        showLiveError(data.error);
      } else {
        renderLiveResults(data.faces);
      }
    } catch (e) {
      showLiveError('Error de conexión con el servidor.');
    } finally {
      isAnalyzing = false;
    }
  }, 'image/jpeg', 0.85);
}

function stopCamera() {
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
  clearTimeout(intervalId);
  clearInterval(countdownId);
  startBtn.disabled = false;
  stopBtn.disabled  = true;
  countdownOvl.style.display = 'none';
  progressBar.style.width = '0%';
  progressBar.style.transition = 'none';
  liveDot.className = 'live-dot';
  liveDot.innerHTML = '<span class="dot"></span> EN ESPERA';
  statusOvl.innerHTML = '<div class="status-icon">⏹</div><div class="status-text">Cámara detenida</div>';
  statusOvl.style.display = 'flex';
}

function renderLiveResults(faces) {
  const now = new Date().toLocaleTimeString('es-CO');
  let html = `<div class="result-timestamp">ACTUALIZADO · ${now}</div>`;

  faces.forEach((face, i) => {
    const emojiMap = { happy:'😄', sad:'😢', angry:'😠', fear:'😨', surprise:'😲', disgust:'🤢', neutral:'😐' };
    const emoji = emojiMap[(face.emocion||'').toLowerCase()] || '😐';
    const emociones = (face.emociones_detalle||[]).sort((a,b)=>b.porcentaje-a.porcentaje);

    html += `
    <div class="face-card" style="animation-delay:${i*0.08}s">
      <div class="face-card-header">
        <span class="face-number">ROSTRO ${i+1}</span>
        <span style="font-size:.82rem;color:var(--text-muted)">${emoji} ${face.emocion||'Neutral'}</span>
      </div>
      <div class="face-card-body">
        <div class="stat-cell">
          <div class="stat-label">Género</div>
          <div class="stat-value">${face.genero}</div>
          <div class="stat-sub">${face.genero_confianza}%</div>
        </div>
        <div class="stat-cell">
          <div class="stat-label">Edad</div>
          <div class="stat-value">${face.edad_estimada}<span style="font-size:.7rem;color:var(--text-muted)"> años</span></div>
          <div class="stat-sub">estimada</div>
        </div>
        <div class="stat-cell">
          <div class="stat-label">Etnia</div>
          <div class="stat-value" style="font-size:.82rem">${face.raza_dominante}</div>
          <div class="stat-sub">&nbsp;</div>
        </div>
      </div>
      ${emociones.length ? `
      <div class="emotions-section">
        <div class="emotions-title">Emociones</div>
        ${emociones.map((e,idx)=>`
          <div class="emotion-row">
            <span class="emotion-name">${cap(e.nombre)}</span>
            <div class="bar-track">
              <div class="bar-fill ${idx===0?'top':''}" style="width:${e.porcentaje}%"></div>
            </div>
            <span class="emotion-pct">${e.porcentaje}%</span>
          </div>`).join('')}
      </div>` : ''}
    </div>`;
  });

  resultsPanel.innerHTML = html;
}

function showLiveError(msg) {
  resultsPanel.innerHTML = `<div class="error-box">⚠ ${msg}</div>`;
}
function showCameraError(msg) {
  statusOvl.innerHTML = `<div class="status-icon">⚠️</div><div class="status-text">${msg}</div>`;
}

// ═══════════════════════════════════════
//  TAB IMAGEN ESTÁTICA
// ═══════════════════════════════════════
const fileInput   = document.getElementById('file-input');
const analyzeBtn  = document.getElementById('analyze-btn');
const previewCont = document.getElementById('preview-container');
const previewImg  = document.getElementById('preview-img');
const imgError    = document.getElementById('img-error');
const annotCont   = document.getElementById('annotated-container');
const annotImg    = document.getElementById('annotated-img');
const imgFaces    = document.getElementById('img-faces');
let selectedFile  = null;

fileInput.addEventListener('change', e => {
  selectedFile = e.target.files[0];
  if (!selectedFile) return;
  previewImg.src = URL.createObjectURL(selectedFile);
  previewCont.style.display = 'block';
  analyzeBtn.disabled = false;
  clearImgResults();
});

document.getElementById('upload-zone').addEventListener('dragover', e => {
  e.preventDefault(); e.currentTarget.style.borderColor = 'var(--accent)';
});
document.getElementById('upload-zone').addEventListener('dragleave', e => {
  e.currentTarget.style.borderColor = '';
});
document.getElementById('upload-zone').addEventListener('drop', e => {
  e.preventDefault(); e.currentTarget.style.borderColor = '';
  const f = e.dataTransfer.files[0];
  if (f && f.type.startsWith('image/')) {
    selectedFile = f;
    previewImg.src = URL.createObjectURL(f);
    previewCont.style.display = 'block';
    analyzeBtn.disabled = false;
    clearImgResults();
  }
});

analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  analyzeBtn.disabled = true;
  analyzeBtn.innerHTML = '<span class="spinner"></span>ANALIZANDO…';
  clearImgResults();
  try {
    const fd = new FormData();
    fd.append('image', selectedFile);
    const resp = await fetch('/analyze', { method: 'POST', body: fd });
    const data = await resp.json();
    if (!resp.ok || data.error) {
      imgError.textContent = '⚠ ' + (data.error || 'Error inesperado');
      imgError.style.display = 'block';
    } else {
      if (data.annotated_image) {
        annotImg.src = 'data:image/jpeg;base64,' + data.annotated_image;
        annotCont.style.display = 'block';
      }
      renderLiveResults_img(data.faces);
    }
  } catch { imgError.textContent = '⚠ No se pudo conectar.'; imgError.style.display = 'block'; }
  finally {
    analyzeBtn.disabled = false;
    analyzeBtn.innerHTML = 'ANALIZAR IMAGEN';
  }
});

function renderLiveResults_img(faces) {
  let html = '';
  faces.forEach((face, i) => {
    const emojiMap = { happy:'😄', sad:'😢', angry:'😠', fear:'😨', surprise:'😲', disgust:'🤢', neutral:'😐' };
    const emoji = emojiMap[(face.emocion||'').toLowerCase()] || '😐';
    const emociones = (face.emociones_detalle||[]).sort((a,b)=>b.porcentaje-a.porcentaje);
    html += `
    <div class="face-card" style="margin-bottom:.85rem;animation-delay:${i*0.08}s">
      <div class="face-card-header">
        <span class="face-number">ROSTRO ${i+1}</span>
        <span style="font-size:.82rem;color:var(--text-muted)">${emoji} ${face.emocion||'Neutral'}</span>
      </div>
      <div class="face-card-body">
        <div class="stat-cell"><div class="stat-label">Género</div><div class="stat-value">${face.genero}</div><div class="stat-sub">${face.genero_confianza}%</div></div>
        <div class="stat-cell"><div class="stat-label">Edad</div><div class="stat-value">${face.edad_estimada}<span style="font-size:.7rem;color:var(--text-muted)"> años</span></div><div class="stat-sub">estimada</div></div>
        <div class="stat-cell"><div class="stat-label">Etnia</div><div class="stat-value" style="font-size:.82rem">${face.raza_dominante}</div><div class="stat-sub">&nbsp;</div></div>
      </div>
      ${emociones.length ? `
      <div class="emotions-section">
        <div class="emotions-title">Emociones</div>
        ${emociones.map((e,idx)=>`
          <div class="emotion-row">
            <span class="emotion-name">${cap(e.nombre)}</span>
            <div class="bar-track"><div class="bar-fill ${idx===0?'top':''}" style="width:${e.porcentaje}%"></div></div>
            <span class="emotion-pct">${e.porcentaje}%</span>
          </div>`).join('')}
      </div>` : ''}
    </div>`;
  });
  imgFaces.innerHTML = html;
}

function clearImgResults() {
  imgError.style.display = 'none';
  annotCont.style.display = 'none';
  imgFaces.innerHTML = '';
}

function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No se recibió ninguna imagen."}), 400
    file = request.files["image"]
    try:
        faces, img_b64 = analyze_from_bytes(file.read())
        return jsonify({"faces": faces, "annotated_image": img_b64})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"App corriendo en http://localhost:{port}")
    app.run(debug=False, host="0.0.0.0", port=port)