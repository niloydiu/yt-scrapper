import os
import logging
from flask import Flask, request, render_template_string, send_file, jsonify
from scraper import get_video_metadata
from transcripts import fetch_transcript_and_translation
from parser import extract_ingredients
from utils import save_records_to_json

APP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)

# Ultra-Premium Modern UI (Linear/Apple Inspired)
INDEX_HTML = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>YouTube Extractor Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
      :root {
        --bg: #030303;
        --card-bg: #0a0a0a;
        --accent: #ffffff;
        --accent-muted: #a1a1aa;
        --border: #27272a;
        --input-bg: #0f0f0f;
        --success: #10b981;
        --error: #ef4444;
      }

      * { margin: 0; padding: 0; box-sizing: border-box; }
      
      body {
        font-family: 'Inter', -apple-system, sans-serif;
        background: var(--bg);
        color: #fafafa;
        line-height: 1.5;
        -webkit-font-smoothing: antialiased;
      }

      .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 24px;
      }

      /* Header & Hero */
      header {
        padding: 80px 0 40px;
        text-align: center;
      }

      .badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        background: #18181b;
        border: 1px solid var(--border);
        border-radius: 100px;
        font-size: 12px;
        font-weight: 600;
        color: var(--accent-muted);
        margin-bottom: 24px;
        letter-spacing: 0.05em;
      }

      h1 {
        font-size: 56px;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 16px;
        background: linear-gradient(to bottom, #fff 0%, #a1a1aa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }

      .subtitle {
        font-size: 18px;
        color: var(--accent-muted);
        max-width: 500px;
        margin: 0 auto 48px;
      }

      /* Features Section */
      .features {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
        margin-bottom: 48px;
        text-align: left;
      }

      @media (max-width: 768px) {
        .features { grid-template-columns: 1fr; }
      }

      .feature-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--border);
        padding: 24px;
        border-radius: 20px;
        transition: all 0.2s;
      }

      .feature-card:hover {
        background: rgba(255,255,255,0.04);
        border-color: #3f3f46;
      }

      .feature-icon {
        width: 40px;
        height: 40px;
        background: #18181b;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
        color: #fff;
        font-size: 20px;
      }

      .feature-card h3 {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 8px;
      }

      .feature-card p {
        font-size: 13px;
        color: var(--accent-muted);
        line-height: 1.6;
      }

      /* Main Input Card */
      .main-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 40px;
        margin-bottom: 64px;
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
      }

      .input-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
        margin-bottom: 32px;
      }

      @media (max-width: 768px) {
        .input-grid { grid-template-columns: 1fr; }
        h1 { font-size: 40px; }
      }

      .field-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .field-group label {
        font-size: 13px;
        font-weight: 600;
        color: var(--accent-muted);
        margin-left: 4px;
      }

      .input-wrapper {
        position: relative;
        display: flex;
        align-items: center;
      }

      .input-wrapper i {
        position: absolute;
        left: 16px;
        color: var(--accent-muted);
        font-size: 18px;
      }

      input {
        width: 100%;
        background: var(--input-bg);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 14px 16px 14px 48px;
        color: #fff;
        font-size: 15px;
        font-family: inherit;
        transition: all 0.2s;
      }

      input:focus {
        outline: none;
        border-color: #52525b;
        background: #141414;
        box-shadow: 0 0 0 4px rgba(255,255,255,0.05);
      }

      .btn-primary {
        width: 100%;
        background: #fff;
        color: #000;
        border: none;
        border-radius: 12px;
        padding: 16px;
        font-size: 16px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
      }

      .btn-primary:hover {
        background: #e4e4e7;
        transform: translateY(-1px);
      }

      .btn-primary:active {
        transform: translateY(0);
      }

      .btn-primary:disabled {
        background: #27272a;
        color: #52525b;
        cursor: not-allowed;
      }

      /* Results Controls */
      .results-header {
        display: none;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 32px;
        padding-bottom: 24px;
        border-bottom: 1px solid var(--border);
        gap: 20px;
        flex-wrap: wrap;
      }

      .search-container {
        position: relative;
        flex: 1;
        min-width: 300px;
      }

      .search-container i {
        position: absolute;
        left: 16px;
        top: 50%;
        transform: translateY(-50%);
        color: var(--accent-muted);
      }

      .search-input {
        padding-left: 44px;
        background: #111;
      }

      .stats-pill {
        display: flex;
        align-items: center;
        gap: 24px;
        background: #111;
        border: 1px solid var(--border);
        padding: 8px 8px 8px 24px;
        border-radius: 100px;
      }

      .stats-count {
        display: flex;
        flex-direction: column;
        line-height: 1;
      }

      .stats-count .num {
        font-size: 18px;
        font-weight: 800;
        color: #fff;
      }

      .stats-count .label {
        font-size: 10px;
        font-weight: 700;
        color: var(--accent-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 2px;
      }

      .btn-download-all {
        background: #fff;
        color: #000;
        padding: 8px 20px;
        border-radius: 100px;
        font-size: 13px;
        font-weight: 700;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: all 0.2s;
      }

      .btn-download-all:hover {
        background: #e4e4e7;
        transform: scale(1.02);
      }

      /* Grid & Cards */
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 24px;
        margin-bottom: 80px;
      }

      .card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 16px;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
      }

      .card:hover {
        border-color: #52525b;
        transform: translateY(-4px);
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5);
      }

      .thumb-box {
        position: relative;
        aspect-ratio: 16/9;
        background: #111;
        cursor: pointer;
      }

      .thumb-box img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .duration {
        position: absolute;
        bottom: 8px;
        right: 8px;
        background: rgba(0,0,0,0.8);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        color: #fff;
      }

      .card-content {
        padding: 16px;
        flex: 1;
        display: flex;
        flex-direction: column;
      }

      .card-title {
        font-size: 14px;
        font-weight: 600;
        color: #fff;
        margin-bottom: 16px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        line-height: 1.4;
        cursor: pointer;
      }

      .card-title:hover {
        color: var(--accent-muted);
      }

      .card-footer {
        margin-top: auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-top: 12px;
        border-top: 1px solid var(--border);
      }

      .video-id {
        font-size: 11px;
        font-family: monospace;
        color: var(--accent-muted);
      }

      .btn-view-yt {
        color: var(--accent-muted);
        text-decoration: none;
        font-size: 14px;
        font-weight: 600;
        transition: color 0.2s;
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .btn-view-yt:hover {
        color: #fff;
      }

      /* Status & Loading */
      .status-area {
        margin-top: 24px;
        display: none;
      }

      .progress-bar {
        height: 4px;
        background: var(--border);
        border-radius: 100px;
        overflow: hidden;
        margin-bottom: 12px;
      }

      .progress-fill {
        height: 100%;
        background: #fff;
        width: 0%;
        transition: width 0.3s;
      }

      .status-text {
        font-size: 13px;
        color: var(--accent-muted);
        text-align: center;
      }

      .fade-in {
        animation: fadeIn 0.5s ease-out forwards;
      }

      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }

      .alert {
        padding: 16px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 500;
        margin-top: 24px;
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .alert-error {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        color: var(--error);
      }
    </style>
  </head>
  <body>
    <div class="container">
      <header>
        <div class="badge">ULTRA PRO EXTRACTOR</div>
        <h1>YouTube Pro</h1>
        <p class="subtitle">The most powerful way to extract metadata and recipe intelligence from YouTube.</p>
        
        <div class="features">
          <div class="feature-card">
            <div class="feature-icon"><i class="bi bi-lightning-charge"></i></div>
            <h3>Deep Metadata</h3>
            <p>Extract 50+ fields including tags, categories, and high-res thumbnails for every video.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon"><i class="bi bi-egg"></i></div>
            <h3>Recipe Intelligence</h3>
            <p>Automatically parse transcripts to extract ingredients and measurements from cooking videos.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon"><i class="bi bi-filetype-json"></i></div>
            <h3>Clean Export</h3>
            <p>Download everything as structured JSON, ready for your database or research projects.</p>
          </div>
        </div>
      </header>

      <div class="main-card">
        <div class="input-grid">
          <div class="field-group">
            <label>YouTube URL</label>
            <div class="input-wrapper">
              <i class="bi bi-link-45deg"></i>
              <input id="urlInput" type="text" placeholder="Channel, Playlist or Video URL">
            </div>
          </div>
          <div class="field-group">
            <label>Filename</label>
            <div class="input-wrapper">
              <i class="bi bi-file-earmark-text"></i>
              <input id="fileInput" type="text" placeholder="Output name" value="extraction">
            </div>
          </div>
        </div>

        <button id="extractBtn" class="btn-primary">
          <i class="bi bi-lightning-charge-fill"></i>
          <span id="btnText">Start Extraction</span>
        </button>

        <div id="statusArea" class="status-area">
          <div class="progress-bar"><div id="progressFill" class="progress-fill"></div></div>
          <div id="statusText" class="status-text">Initializing...</div>
        </div>

        <div id="errorAlert" class="alert alert-error" style="display: none;">
          <i class="bi bi-exclamation-circle-fill"></i>
          <span id="errorMsg"></span>
        </div>
      </div>

      <div id="resultsHeader" class="results-header">
        <div class="search-container">
          <i class="bi bi-search"></i>
          <input id="searchInput" class="search-input" type="text" placeholder="Search videos...">
        </div>
        
        <div class="stats-pill">
          <div class="stats-count" id="countDisplay">
            <span class="num">0</span>
            <span class="label">Videos Extracted</span>
          </div>
          <a href="#" id="dlAllBtn" class="btn-download-all" target="_blank">
            <i class="bi bi-cloud-arrow-down-fill"></i>
            Download JSON
          </a>
        </div>
      </div>

      <div id="grid" class="grid"></div>
    </div>

    <script>
      const extractBtn = document.getElementById('extractBtn');
      const btnText = document.getElementById('btnText');
      const urlInput = document.getElementById('urlInput');
      const fileInput = document.getElementById('fileInput');
      const statusArea = document.getElementById('statusArea');
      const statusText = document.getElementById('statusText');
      const progressFill = document.getElementById('progressFill');
      const errorAlert = document.getElementById('errorAlert');
      const errorMsg = document.getElementById('errorMsg');
      const resultsHeader = document.getElementById('resultsHeader');
      const searchInput = document.getElementById('searchInput');
      const countDisplay = document.getElementById('countDisplay');
      const dlAllBtn = document.getElementById('dlAllBtn');
      const grid = document.getElementById('grid');

      let allVideos = [];

      function createCard(video) {
        const card = document.createElement('div');
        card.className = 'card fade-in';
        card.innerHTML = `
          <div class="thumb-box" onclick="window.open('${video.youtubeVideoLink}', '_blank')">
            <img src="${video.thumbnail}" alt="" onerror="this.src='https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=400&q=80'">
            <div class="duration">${video.duration}</div>
          </div>
          <div class="card-content">
            <div class="card-title" onclick="window.open('${video.youtubeVideoLink}', '_blank')">${video.title}</div>
            <div class="card-footer">
              <a href="/video/${video.videoId}" class="btn-view-yt" target="_blank" style="color: #fff;">
                <i class="bi bi-egg-fill"></i> Ingredients
              </a>
              <a href="${video.youtubeVideoLink}" class="btn-view-yt" target="_blank">
                <i class="bi bi-youtube"></i> YouTube
              </a>
            </div>
          </div>
        `;
        return card;
      }

      async function startExtraction() {
        const url = urlInput.value.trim();
        let filename = fileInput.value.trim() || 'extraction';
        if (!filename.endsWith('.json')) filename += '.json';

        if (!url) {
          showError('Please enter a valid YouTube URL');
          return;
        }

        // Reset UI
        errorAlert.style.display = 'none';
        statusArea.style.display = 'block';
        extractBtn.disabled = true;
        btnText.textContent = 'Extracting...';
        progressFill.style.width = '20%';
        statusText.textContent = 'Connecting to YouTube...';
        grid.innerHTML = '';
        resultsHeader.style.display = 'none';

        try {
          const response = await fetch('/api/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel: url, filename })
          });

          if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Extraction failed');
          }

          const data = await response.json();
          allVideos = data.results;
          
          progressFill.style.width = '100%';
          statusText.textContent = `Successfully extracted ${data.count} videos`;
          
          renderResults(allVideos);
          
          resultsHeader.style.display = 'flex';
          countDisplay.querySelector('.num').textContent = data.count;
          dlAllBtn.href = `/download/${data.filename}`;

          setTimeout(() => {
            statusArea.style.display = 'none';
            extractBtn.disabled = false;
            btnText.textContent = 'Start Extraction';
          }, 2000);

        } catch (err) {
          showError(err.message);
          statusArea.style.display = 'none';
          extractBtn.disabled = false;
          btnText.textContent = 'Start Extraction';
        }
      }

      function renderResults(videos) {
        grid.innerHTML = '';
        videos.forEach(v => grid.appendChild(createCard(v)));
      }

      function showError(msg) {
        errorMsg.textContent = msg;
        errorAlert.style.display = 'flex';
      }

      searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = allVideos.filter(v => v.title.toLowerCase().includes(term));
        renderResults(filtered);
        countDisplay.querySelector('.num').textContent = filtered.length;
      });

      extractBtn.addEventListener('click', startExtraction);
      urlInput.addEventListener('keypress', (e) => e.key === 'Enter' && startExtraction());
    </script>
  </body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/api/extract', methods=['POST'])
def api_extract():
    payload = request.get_json(silent=True) or {}
    channel = (payload.get('channel') or '').strip()
    filename = (payload.get('filename') or 'extraction.json').strip()
    
    if not channel:
        return jsonify({'error': 'Missing URL'}), 400
    
    if not filename.endswith('.json'):
        filename += '.json'

    try:
        videos = get_video_metadata(channel)
        for idx, video in enumerate(videos, start=1):
            video['id'] = idx
        
        out_file = os.path.join(DATA_DIR, filename)
        save_records_to_json(videos, out_file)
        
        return jsonify({
            'count': len(videos),
            'results': videos,
            'filename': filename
        })
    except Exception as e:
        log.exception('Extraction failed')
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path): return 'Not found', 404
    return send_file(file_path, as_attachment=True)

# Recipe Intelligence View
INGREDIENTS_HTML = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Recipe Intelligence - {{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
      :root {
        --bg: #030303;
        --card-bg: #0a0a0a;
        --accent: #ffffff;
        --accent-muted: #a1a1aa;
        --border: #27272a;
      }
      body {
        font-family: 'Inter', sans-serif;
        background: var(--bg);
        color: #fafafa;
        padding: 40px 20px;
        line-height: 1.6;
      }
      .container { max-width: 800px; margin: 0 auto; }
      .header { margin-bottom: 40px; }
      .badge {
        display: inline-block;
        padding: 4px 12px;
        background: #18181b;
        border: 1px solid var(--border);
        border-radius: 100px;
        font-size: 12px;
        font-weight: 600;
        color: var(--accent-muted);
        margin-bottom: 16px;
      }
      h1 { font-size: 32px; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.02em; }
      .meta { color: var(--accent-muted); font-size: 14px; margin-bottom: 32px; }
      
      .section {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 32px;
      }
      .section-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .ingredient-list {
        list-style: none;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }
      @media (max-width: 600px) { .ingredient-list { grid-template-columns: 1fr; } }
      .ingredient-item {
        background: #111;
        border: 1px solid var(--border);
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .ingredient-item i { color: var(--accent-muted); }
      
      .no-data {
        text-align: center;
        padding: 40px;
        color: var(--accent-muted);
      }
      .btn-back {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: var(--accent-muted);
        text-decoration: none;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 24px;
      }
      .btn-back:hover { color: #fff; }
    </style>
  </head>
  <body>
    <div class="container">
      <a href="javascript:window.close()" class="btn-back"><i class="bi bi-arrow-left"></i> Close Tab</a>
      
      <div class="header">
        <div class="badge">RECIPE INTELLIGENCE</div>
        <h1>{{ title }}</h1>
        <div class="meta">Video ID: {{ video_id }}</div>
      </div>

      <div class="section">
        <div class="section-title">
          <i class="bi bi-egg-fill"></i> Extracted Ingredients
        </div>
        {% if ingredients %}
          <ul class="ingredient-list">
            {% for item in ingredients %}
              <li class="ingredient-item">
                <i class="bi bi-check2-circle"></i>
                {{ item }}
              </li>
            {% endfor %}
          </ul>
        {% else %}
          <div class="no-data">
            <i class="bi bi-search" style="font-size: 24px; display: block; margin-bottom: 12px;"></i>
            No ingredients could be automatically extracted from the transcript.
          </div>
        {% endif %}
      </div>

      <div class="section">
        <div class="section-title">
          <i class="bi bi-info-circle-fill"></i> How it works
        </div>
        <p style="font-size: 14px; color: var(--accent-muted);">
          Our AI-powered engine analyzes the video transcript in real-time, identifying culinary terms, measurements, and food items. 
          This allows you to quickly see what you need without watching the entire video.
        </p>
      </div>
    </div>
  </body>
</html>
'''

@app.route('/video/<video_id>')
def video_details(video_id):
    try:
        # Fetch transcript
        transcript_data = fetch_transcript_and_translation(video_id)
        full_text = " ".join([t['text'] for t in transcript_data])
        
        # Extract ingredients
        ingredients = extract_ingredients(full_text)
        
        # We don't have the title here easily without re-scraping, 
        # but we can just show the ID or a placeholder for now.
        # In a real app, we'd pass the title from the frontend or cache it.
        return render_template_string(INGREDIENTS_HTML, 
                                    title="Video Recipe Analysis", 
                                    video_id=video_id, 
                                    ingredients=ingredients)
    except Exception as e:
        return f"Error analyzing video: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
