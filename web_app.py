"""
web_app.py

Modern Flask web UI for extracting all videos from a YouTube channel or
playlist URL. Transcripts are intentionally not fetched. Each record
includes `videoId` and `thumbnail`. Results are saved to `data/extracted.json`.
The UI uses Bootstrap and AJAX for a smooth, modern experience.
"""
import os
from flask import Flask, request, render_template_string, send_file, jsonify

from scraper import get_video_urls
from utils import save_records_to_json


APP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUT_FILE = os.path.join(DATA_DIR, "extracted.json")

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>YouTube Recipe Extractor</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { background: #f7fafc; }
      .hero { background: linear-gradient(90deg,#0ea5e9, #2563eb); color: white; padding: 28px 20px; border-radius: 12px; }
      .card-float { margin-top: -36px; box-shadow: 0 8px 30px rgba(16,24,40,0.08); }
      .thumb { width:160px; height:auto; border-radius:8px }
      .muted { color:#6b7280 }
      pre.path { background:#111827; color:#f8fafc; padding:6px 10px; border-radius:6px; display:inline-block }
    </style>
  </head>
  <body>
    <div class="container py-4">
      <div class="hero">
        <div class="container d-flex align-items-center justify-content-between">
          <div>
            <h2 class="mb-0">YouTube Recipe Extractor</h2>
            <div class="muted">Extract video list & thumbnails — transcripts are skipped</div>
          </div>
          <div>
            <a href="/download" class="btn btn-outline-light">Download JSON</a>
          </div>
        </div>
      </div>

      <div class="card card-body card-float">
        <div class="row g-3 align-items-center">
          <div class="col-md-9">
            <input id="channelInput" class="form-control form-control-lg" placeholder="YouTube channel or playlist URL" aria-label="channel">
          </div>
          <div class="col-md-3 d-grid">
            <button id="extractBtn" class="btn btn-primary btn-lg">Extract All Videos</button>
          </div>
        </div>
        <div class="mt-3">
          <div id="statusText" class="muted">Saved JSON path: <code class="path">data/extracted.json</code></div>
        </div>
      </div>

      <div id="results" class="mt-4"></div>
    </div>

    <script>
      const btn = document.getElementById('extractBtn');
      const input = document.getElementById('channelInput');
      const results = document.getElementById('results');
      const statusText = document.getElementById('statusText');

      function renderGrid(items) {
        if (!items || items.length === 0) {
          results.innerHTML = '<div class="alert alert-warning">No videos found.</div>';
          return;
        }
        let html = '<div class="row row-cols-1 row-cols-md-2 g-3">';
        for (const r of items) {
          html += `
            <div class="col">
              <div class="card h-100">
                <div class="row g-0">
                  <div class="col-auto p-3">
                    <a href="${r.youtubeVideoLink}" target="_blank"><img src="${r.thumbnail}" class="thumb" alt="thumb"></a>
                  </div>
                  <div class="col">
                    <div class="card-body">
                      <h5 class="card-title"><a href="${r.youtubeVideoLink}" target="_blank">${r.youtubeVideoLink}</a></h5>
                      <p class="card-text"><small class="text-muted">Thumbnail URL:</small><br><code style="word-break:break-all">${r.thumbnail}</code></p>
                    </div>
                  </div>
                </div>
              </div>
            </div>`;
        }
        html += '</div>';
        results.innerHTML = html;
      }

      btn.addEventListener('click', async () => {
        const channel = input.value.trim();
        if (!channel) return alert('Please enter channel URL');
        btn.disabled = true; btn.textContent = 'Extracting...';
        statusText.textContent = 'Working — extracting video list...';

        try {
          const resp = await fetch('/api/extract', {
            method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({channel})
          });
          if (!resp.ok) throw new Error('Server error: ' + resp.status);
          const data = await resp.json();
          statusText.textContent = `Saved ${data.count} records to: ${data.out_file}`;
          renderGrid(data.results);
          btn.textContent = 'Done';
        } catch (err) {
          statusText.textContent = 'Error: ' + err.message;
          results.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
          btn.textContent = 'Extract All Videos';
        } finally { btn.disabled = false; }
      });
    </script>
  </body>
</html>
"""

RESULT_HTML = """
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Extraction Results</title></head>
  <body>
    <h1>Extraction Results</h1>
    <p>Processed {{ count }} videos. Saved to {{ out_file }}</p>
    <ul>
      {% for r in results %}
        <li><a href="{{ r.youtubeVideoLink }}">{{ r.youtubeVideoLink }}</a> — <img src="{{ r.thumbnail }}" width="120"></li>
      {% endfor %}
    </ul>
    <p><a href="/">Back</a></p>
  </body>
</html>
"""


@app.route('/', methods=['GET'])
def index():
    return render_template_string(INDEX_HTML)


@app.route('/extract', methods=['POST'])
def extract():
    # Backwards-compatible HTML form handler
    channel = request.form.get('channel', '').strip()
    if not channel:
        return 'Please provide a YouTube channel URL', 400
    resp = _do_extract(channel)
    return render_template_string(RESULT_HTML, count=resp['count'], results=resp['results'], out_file=resp['out_file'])


@app.route('/api/extract', methods=['POST'])
def api_extract():
    data = request.get_json() if request.is_json else {'channel': request.form.get('channel', '')}
    channel = (data.get('channel') or '').strip()
    if not channel:
        return jsonify({'error': 'Missing channel'}), 400
    resp = _do_extract(channel)
    return jsonify(resp)


def _do_extract(channel):
    video_urls = get_video_urls(channel)
    results = []
    from urllib.parse import urlparse, parse_qs
    for idx, vurl in enumerate(video_urls, start=1):
        vid = None
        try:
            parsed = urlparse(vurl)
            q = parse_qs(parsed.query)
            vid = q.get('v', [None])[0]
            if not vid:
                vid = parsed.path.split('/')[-1]
        except Exception:
            vid = None
        thumbnail = f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg' if vid else ''
        record = {
            'id': idx,
            'youtubeVideoLink': vurl,
            'videoId': vid,
            'thumbnail': thumbnail,
            'transcript': '',
            'translation': '',
            'ingredients': [],
        }
        results.append(record)
    save_records_to_json(results, OUT_FILE)
    simple = [{'youtubeVideoLink': r['youtubeVideoLink'], 'thumbnail': r['thumbnail']} for r in results]
    return {'count': len(results), 'results': simple, 'out_file': OUT_FILE}


@app.route('/download')
def download():
    if not os.path.exists(OUT_FILE):
        return 'No extraction file yet.', 404
    return send_file(OUT_FILE, as_attachment=True, download_name=os.path.basename(OUT_FILE))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=5000, type=int)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=True)
"""
web_app.py

Simple Flask web UI for extracting up to 3 video links from a YouTube
channel URL. This intentionally does NOT fetch transcripts (transcript and
translation fields are left empty). Results are saved to `data/extracted.json`
inside the project directory.
"""
import os
from flask import Flask, request, render_template_string, send_file, jsonify

from scraper import get_video_urls
INDEX_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>YouTube Recipe Extractor</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { background: #f7fafc; }
      .hero { background: linear-gradient(90deg,#0ea5e9, #2563eb); color: white; padding: 28px 20px; border-radius: 12px; }
      .card-float { margin-top: -36px; box-shadow: 0 8px 30px rgba(16,24,40,0.08); }
      .thumb { width:160px; height:auto; border-radius:8px }
      .muted { color:#6b7280 }
      pre.path { background:#111827; color:#f8fafc; padding:6px 10px; border-radius:6px; display:inline-block }
    </style>
  </head>
  <body>
    <div class="container py-4">
      <div class="hero">
        <div class="container d-flex align-items-center justify-content-between">
          <div>
            <h2 class="mb-0">YouTube Recipe Extractor</h2>
            <div class="muted">Extract video list & thumbnails — transcripts are skipped</div>
          </div>
          <div>
            <a href="/download" class="btn btn-outline-light">Download JSON</a>
          </div>
        </div>
      </div>

      <div class="card card-body card-float">
        <div class="row g-3 align-items-center">
          <div class="col-md-9">
            <input id="channelInput" class="form-control form-control-lg" placeholder="YouTube channel or playlist URL" aria-label="channel">
          </div>
          <div class="col-md-3 d-grid">
            <button id="extractBtn" class="btn btn-primary btn-lg">Extract All Videos</button>
          </div>
        </div>
        <div class="mt-3">
          <div id="statusText" class="muted">Saved JSON path: <code class="path">data/extracted.json</code></div>
        </div>
      </div>

      <div id="results" class="mt-4"></div>
    </div>

    <script>
      const btn = document.getElementById('extractBtn');
      const input = document.getElementById('channelInput');
      const results = document.getElementById('results');
      const statusText = document.getElementById('statusText');

      function renderGrid(items) {
        if (!items || items.length === 0) {
          results.innerHTML = '<div class="alert alert-warning">No videos found.</div>';
          return;
        }
        let html = '<div class="row row-cols-1 row-cols-md-2 g-3">';
        for (const r of items) {
          html += `
            <div class="col">
              <div class="card h-100">
                <div class="row g-0">
                  <div class="col-auto p-3">
                    <a href="${r.youtubeVideoLink}" target="_blank"><img src="${r.thumbnail}" class="thumb" alt="thumb"></a>
                  </div>
                  <div class="col">
                    <div class="card-body">
                      <h5 class="card-title"><a href="${r.youtubeVideoLink}" target="_blank">${r.youtubeVideoLink}</a></h5>
                      <p class="card-text"><small class="text-muted">Thumbnail URL:</small><br><code style="word-break:break-all">${r.thumbnail}</code></p>
                    </div>
                  </div>
                </div>
              </div>
            </div>`;
        }
        html += '</div>';
        results.innerHTML = html;
      }

      btn.addEventListener('click', async () => {
        const channel = input.value.trim();
        if (!channel) return alert('Please enter channel URL');
        btn.disabled = true; btn.textContent = 'Extracting...';
        statusText.textContent = 'Working — extracting video list...';

        try {
          const resp = await fetch('/api/extract', {
            method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({channel})
          });
          if (!resp.ok) throw new Error('Server error: ' + resp.status);
          const data = await resp.json();
          statusText.textContent = `Saved ${data.count} records to: ${data.out_file}`;
          renderGrid(data.results);
          btn.textContent = 'Done';
        } catch (err) {
          statusText.textContent = 'Error: ' + err.message;
          results.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
          btn.textContent = 'Extract All Videos';
        } finally { btn.disabled = false; }
      });
    </script>
  </body>
</html>
"""
      # Do NOT fetch transcripts; leave fields empty
      transcript_text = ""
      translation_text = ""

      # derive thumbnail URL from video id (standard YouTube thumbnail URL)
      vid = None
      try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(vurl)
        q = parse_qs(parsed.query)
        vid = q.get("v", [None])[0]
        if not vid:
          vid = parsed.path.split("/")[-1]
      except Exception:
        vid = None

      thumbnail = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else ""

      ingredients = []

      record = {
        "id": idx,
        "youtubeVideoLink": vurl,
        "videoId": vid,
        "thumbnail": thumbnail,
        "transcript": transcript_text,
        "translation": translation_text,
        "ingredients": ingredients,
      }
      results.append(record)

    # Save results into project `data/extracted.json`
    save_records_to_json(results, OUT_FILE)

    # Prepare simple dicts for template rendering
    display_results = []
    for r in results:
      display_results.append({
        "youtubeVideoLink": r["youtubeVideoLink"],
        "thumbnail": r.get("thumbnail", ""),
      })

    return render_template_string(RESULT_HTML, count=len(results), results=display_results, out_file=OUT_FILE)


@app.route('/download')
def download():
    if not os.path.exists(OUT_FILE):
        return "No extraction file yet.", 404
    return send_file(OUT_FILE, as_attachment=True, download_name=os.path.basename(OUT_FILE))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
