import os
import logging
from flask import Flask, request, render_template_string, send_file, jsonify
from scraper import get_video_metadata
from utils import save_records_to_json
from yt_dlp import YoutubeDL

APP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)

# Premium Modern UI
INDEX_HTML = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>YouTube Video Extractor - Premium Edition</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      
      body {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        background: #0a0e27;
        color: #e4e7eb;
        min-height: 100vh;
        overflow-x: hidden;
      }
      
      body::before {
        content: '';
        position: fixed;
        inset: 0;
        background: radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3), transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(99, 102, 241, 0.3), transparent 50%);
        z-index: -1;
        animation: gradientMove 15s ease infinite;
      }
      
      @keyframes gradientMove {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
      }
      
      .container-main {
        max-width: 1600px;
        margin: 0 auto;
        padding: 40px 20px;
      }
      
      .hero-section {
        text-align: center;
        margin-bottom: 50px;
      }
      
      .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 8px 20px;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #a5b4fc;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
      }
      
      .hero-title {
        font-size: 4.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 50%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 16px;
        letter-spacing: -2px;
        line-height: 1.1;
      }
      
      .hero-subtitle {
        font-size: 1.25rem;
        color: #9ca3af;
        max-width: 600px;
        margin: 0 auto;
      }
      
      .glass-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 48px;
        margin-bottom: 40px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
      }
      
      .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
      }
      
      .input-group-premium {
        margin-bottom: 28px;
      }
      
      .input-group-premium label {
        display: flex;
        align-items: center;
        font-weight: 600;
        margin-bottom: 12px;
        color: #f3f4f6;
        font-size: 0.95rem;
      }
      
      .input-group-premium label i {
        margin-right: 8px;
        color: #6366f1;
        font-size: 1.1rem;
      }
      
      .input-group-premium input {
        width: 100%;
        padding: 18px 24px;
        background: rgba(30, 41, 59, 0.5);
        border: 1.5px solid rgba(99, 102, 241, 0.3);
        border-radius: 14px;
        font-size: 1rem;
        color: #f3f4f6;
        transition: all 0.3s;
        font-weight: 500;
      }
      
      .input-group-premium input::placeholder {
        color: #6b7280;
      }
      
      .input-group-premium input:focus {
        outline: none;
        background: rgba(30, 41, 59, 0.8);
        border-color: #6366f1;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15), 0 10px 30px rgba(99, 102, 241, 0.2);
        transform: translateY(-2px);
      }
      
      .btn-extract {
        width: 100%;
        padding: 20px;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #6366f1 100%);
        background-size: 200% 100%;
        border: none;
        border-radius: 14px;
        color: white;
        font-weight: 700;
        font-size: 1.15rem;
        cursor: pointer;
        transition: all 0.4s;
        box-shadow: 0 10px 40px rgba(99, 102, 241, 0.4);
        position: relative;
        overflow: hidden;
      }
      
      .btn-extract::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
      }
      
      .btn-extract:hover:not(:disabled)::before {
        left: 100%;
      }
      
      .btn-extract:hover:not(:disabled) {
        background-position: 100% 0;
        transform: translateY(-3px);
        box-shadow: 0 15px 50px rgba(99, 102, 241, 0.6);
      }
      
      .btn-extract:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      
      .status-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 28px;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.1));
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 14px;
        margin-top: 28px;
        backdrop-filter: blur(10px);
      }
      
      .status-text {
        color: #e0e7ff;
        font-weight: 600;
        display: flex;
        align-items: center;
      }
      
      .status-text i {
        margin-right: 10px;
        color: #6366f1;
      }
      
      .count-badge {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        padding: 8px 20px;
        border-radius: 50px;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
      }

      .sticky-controls {
        position: sticky;
        top: 0;
        z-index: 100;
        background: rgba(10, 14, 39, 0.8);
        backdrop-filter: blur(20px);
        padding: 20px 0;
        margin-bottom: 30px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: none;
      }

      .search-input {
        width: 100%;
        padding: 15px 25px;
        background: rgba(30, 41, 59, 0.5);
        border: 1.5px solid rgba(99, 102, 241, 0.3);
        border-radius: 14px;
        font-size: 1rem;
        color: #f3f4f6;
        transition: all 0.3s;
        font-weight: 500;
      }

      .search-input:focus {
        outline: none;
        border-color: #6366f1;
        background: rgba(30, 41, 59, 0.8);
      }
      
      .results-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
        gap: 28px;
      }
      
      .video-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        overflow: hidden;
        transition: all 0.4s;
        cursor: pointer;
        position: relative;
        display: flex;
        flex-direction: column;
      }
      
      .video-card::before {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
        opacity: 0;
        transition: opacity 0.4s;
      }
      
      .video-card:hover {
        transform: translateY(-8px) scale(1.02);
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.3);
      }
      
      .video-card:hover::before {
        opacity: 1;
      }
      
      .video-thumbnail-container {
        position: relative;
        overflow: hidden;
        height: 200px;
        background: linear-gradient(135deg, #1e293b, #0f172a);
      }
      
      .video-thumbnail {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.4s;
      }
      
      .video-card:hover .video-thumbnail {
        transform: scale(1.1);
      }
      
      .video-duration-overlay {
        position: absolute;
        bottom: 12px;
        right: 12px;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(10px);
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 700;
        color: white;
        display: flex;
        align-items: center;
      }
      
      .video-duration-overlay i {
        margin-right: 5px;
      }
      
      .video-info {
        padding: 20px;
        position: relative;
        z-index: 1;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
      }
      
      .video-title {
        font-weight: 700;
        font-size: 1.05rem;
        color: #f3f4f6;
        margin-bottom: 12px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        line-height: 1.5;
      }

      .video-meta-bottom {
        margin-top: auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .video-id-badge {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.3);
        color: #a5b4fc;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'Courier New', monospace;
      }

      .btn-card-download {
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34d399;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        transition: all 0.3s;
        text-decoration: none;
        display: flex;
        align-items: center;
      }

      .btn-card-download:hover {
        background: #10b981;
        color: white;
        transform: scale(1.05);
      }

      .btn-card-download i {
        margin-right: 5px;
      }
      
      .download-section {
        text-align: center;
        margin-bottom: 40px;
        padding: 30px;
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
      }
      
      .btn-download {
        display: inline-flex;
        align-items: center;
        padding: 18px 40px;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 14px;
        font-weight: 700;
        font-size: 1.1rem;
        text-decoration: none;
        transition: all 0.4s;
        box-shadow: 0 10px 40px rgba(16, 185, 129, 0.4);
      }
      
      .btn-download:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 50px rgba(16, 185, 129, 0.6);
        color: white;
      }
      
      .btn-download i {
        margin-right: 10px;
      }
      
      .spinner {
        animation: spin 1s linear infinite;
      }
      
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      
      .pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
      }
      
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
      
      .fade-in {
        animation: fadeInUp 0.6s;
      }
      
      @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
      }
      
      .alert-premium {
        padding: 20px 24px;
        border-radius: 14px;
        margin-top: 24px;
        border-left: 4px solid;
        backdrop-filter: blur(20px);
        font-weight: 500;
      }
      
      .alert-danger {
        background: rgba(239, 68, 68, 0.1);
        border-color: #ef4444;
        color: #fca5a5;
      }
      
      @media (max-width: 768px) {
        .hero-title { font-size: 2.5rem; }
        .glass-card { padding: 28px; }
        .results-grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="container-main">
      <div class="hero-section fade-in">
        <div class="hero-badge">
          <i class="bi bi-stars"></i> PREMIUM EDITION
        </div>
        <h1 class="hero-title">YouTube Extractor</h1>
        <p class="hero-subtitle">Extract complete metadata from ALL videos in any YouTube channel, playlist, or single video</p>
      </div>

      <div class="glass-card fade-in">
        <div class="input-group-premium">
          <label for="channelInput">
            <i class="bi bi-youtube"></i> YouTube URL (Channel, Playlist, or Video)
          </label>
          <input 
            id="channelInput" 
            type="text" 
            placeholder="https://www.youtube.com/@channelname or video URL"
            autocomplete="off"
          >
        </div>

        <div class="input-group-premium">
          <label for="filenameInput">
            <i class="bi bi-file-earmark-code"></i> Output Filename
          </label>
          <input 
            id="filenameInput" 
            type="text" 
            placeholder="my-channel-videos (no extension needed)"
            value="videos"
            autocomplete="off"
          >
        </div>

        <button id="extractBtn" class="btn-extract">
          <i class="bi bi-rocket-takeoff-fill"></i>
          <span id="btnText">EXTRACT VIDEOS</span>
        </button>

        <div id="statusBar" class="status-bar" style="display: none;">
          <div class="status-text">
            <i class="bi bi-hourglass-split pulse"></i>
            <span id="statusText">Ready</span>
          </div>
          <div class="count-badge" id="countLabel">0 videos</div>
        </div>
      </div>

      <div id="stickyControls" class="sticky-controls">
        <div class="container">
          <div class="row align-items-center">
            <div class="col-md-8">
              <input id="searchInput" class="search-input" placeholder="Search extracted videos by title...">
            </div>
            <div class="col-md-4 text-end">
              <div id="countLabelSticky" class="count-badge">0 videos</div>
            </div>
          </div>
        </div>
      </div>

      <div id="downloadSection" class="download-section" style="display: none;">
        <h3 style="color: #f3f4f6; margin-bottom: 20px; font-weight: 700;">
          <i class="bi bi-check-circle-fill" style="color: #10b981;"></i> Extraction Complete!
        </h3>
        <a href="#" id="downloadLink" class="btn-download">
          <i class="bi bi-cloud-download-fill"></i> DOWNLOAD FULL JSON
        </a>
      </div>

      <div id="results" class="results-grid"></div>
    </div>

    <script>
      const btn = document.getElementById('extractBtn');
      const btnText = document.getElementById('btnText');
      const input = document.getElementById('channelInput');
      const filenameInput = document.getElementById('filenameInput');
      const results = document.getElementById('results');
      const statusBar = document.getElementById('statusBar');
      const statusText = document.getElementById('statusText');
      const countLabel = document.getElementById('countLabel');
      const countLabelSticky = document.getElementById('countLabelSticky');
      const downloadSection = document.getElementById('downloadSection');
      const downloadLink = document.getElementById('downloadLink');
      const stickyControls = document.getElementById('stickyControls');
      const searchInput = document.getElementById('searchInput');

      let allVideos = [];

      function createVideoCard(video) {
        const card = document.createElement('div');
        card.className = 'video-card fade-in';
        card.dataset.title = video.title.toLowerCase();
        
        card.innerHTML = `
          <div class="video-thumbnail-container" onclick="window.open('${video.youtubeVideoLink}', '_blank')">
            <img src="${video.thumbnail}" alt="${escapeHtml(video.title)}" class="video-thumbnail" 
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22360%22 height=%22200%22%3E%3Crect fill=%22%231e293b%22 width=%22360%22 height=%22200%22/%3E%3C/svg%3E'">
            <div class="video-duration-overlay">
              <i class="bi bi-play-fill"></i> ${video.duration}
            </div>
          </div>
          <div class="video-info">
            <div class="video-title" onclick="window.open('${video.youtubeVideoLink}', '_blank')">${escapeHtml(video.title)}</div>
            <div class="video-meta-bottom">
              <span class="video-id-badge">${video.videoId}</span>
              <a href="/api/download_single?url=${encodeURIComponent(video.youtubeVideoLink)}" class="btn-card-download" target="_blank">
                <i class="bi bi-download"></i> Download
              </a>
            </div>
          </div>
        `;
        
        return card;
      }

      function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
      }

      function showAlert(message, type = 'danger') {
        const alert = document.createElement('div');
        alert.className = `alert-premium alert-${type} fade-in`;
        alert.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> ${message}`;
        results.innerHTML = '';
        results.appendChild(alert);
      }

      async function extract() {
        const channel = input.value.trim();
        const filename = filenameInput.value.trim() || 'videos';
        
        if (!channel) {
          showAlert('Please enter a YouTube URL');
          input.focus();
          return;
        }

        const filenameToSend = filename.endsWith('.json') ? filename : filename + '.json';

        btn.disabled = true;
        btnText.innerHTML = '<i class="bi bi-arrow-repeat spinner"></i> EXTRACTING...';
        statusBar.style.display = 'flex';
        statusText.textContent = 'Fetching video metadata...';
        results.innerHTML = '';
        downloadSection.style.display = 'none';
        stickyControls.style.display = 'none';
        allVideos = [];

        try {
          const resp = await fetch('/api/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel, filename: filenameToSend })
          });

          if (!resp.ok) {
            const err = await resp.json().catch(() => null);
            throw new Error(err?.error || `Server error: ${resp.status}`);
          }

          const data = await resp.json();
          allVideos = data.results;
          
          statusText.innerHTML = `<i class="bi bi-check-circle-fill" style="color: #10b981;"></i> Successfully extracted ${data.count} videos`;
          countLabel.textContent = `${data.count} videos`;
          countLabelSticky.textContent = `${data.count} videos`;
          
          renderVideos(allVideos);

          downloadSection.style.display = 'block';
          stickyControls.style.display = 'block';
          downloadLink.href = `/download/${data.filename}`;
          
          btnText.innerHTML = '<i class="bi bi-check-circle-fill"></i> COMPLETE';
          setTimeout(() => {
            btn.disabled = false;
            btnText.innerHTML = '<i class="bi bi-rocket-takeoff-fill"></i> EXTRACT VIDEOS';
          }, 3000);

        } catch (e) {
          statusText.innerHTML = '<i class="bi bi-x-circle-fill" style="color: #ef4444;"></i> Error';
          showAlert(`Error: ${e.message}`);
          btn.disabled = false;
          btnText.innerHTML = '<i class="bi bi-rocket-takeoff-fill"></i> EXTRACT VIDEOS';
        }
      }

      function renderVideos(videos) {
        results.innerHTML = '';
        videos.forEach((video, index) => {
          setTimeout(() => {
            results.appendChild(createVideoCard(video));
          }, Math.min(index * 30, 1000));
        });
      }

      searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = allVideos.filter(v => v.title.toLowerCase().includes(term));
        
        // Clear and re-render without animation for speed
        results.innerHTML = '';
        filtered.forEach(video => {
          results.appendChild(createVideoCard(video));
        });
        countLabelSticky.textContent = `${filtered.length} videos`;
      });

      btn.addEventListener('click', extract);
      input.addEventListener('keydown', (e) => { if (e.key === 'Enter') extract(); });
      filenameInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') extract(); });
    </script>
  </body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


@app.route('/api/extract', methods=['POST'])
def api_extract():
    """Extract video metadata from YouTube channel/playlist/video."""
    payload = request.get_json(silent=True) or {}
    channel = (payload.get('channel') or '').strip()
    filename = (payload.get('filename') or 'videos.json').strip()
    
    if not channel:
        return jsonify({'error': 'Missing channel parameter'}), 400
    
    if not filename.endswith('.json'):
        filename += '.json'

    try:
        log.info(f"Extracting videos from: {channel}")
        videos = get_video_metadata(channel)
        log.info(f"Found {len(videos)} videos")
        
        for idx, video in enumerate(videos, start=1):
            video['id'] = idx
        
        out_file = os.path.join(DATA_DIR, filename)
        save_records_to_json(videos, out_file)
        log.info(f"Saved {len(videos)} videos to: {out_file}")
        
        return jsonify({
            'count': len(videos),
            'results': videos,
            'filename': filename,
            'out_file': out_file
        })
        
    except Exception as e:
        log.exception('Extraction failed')
        return jsonify({'error': f'Failed to extract videos: {str(e)}'}), 500


@app.route('/api/download_single')
def download_single():
    """Get a direct download link for a single video."""
    video_url = request.args.get('url')
    if not video_url:
        return 'Missing URL', 400
        
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = info.get('url')
            if download_url:
                from flask import redirect
                return redirect(download_url)
            else:
                return 'Could not find download URL', 404
    except Exception as e:
        return f'Error: {str(e)}', 500


@app.route('/download/<filename>')
def download(filename):
    """Download the generated JSON file."""
    file_path = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(file_path):
        return 'File not found', 404
    
    return send_file(file_path, as_attachment=True, download_name=filename)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 YouTube Video Extractor - PREMIUM EDITION")
    print("="*60)
    print("📍 Server: http://127.0.0.1:8000")
    print("📁 Output: ./data/")
    print("✨ Features: Extracts ALL videos + metadata")
    print("="*60 + "\n")
    app.run(host='127.0.0.1', port=8000, debug=True)
