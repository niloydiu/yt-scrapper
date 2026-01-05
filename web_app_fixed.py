import os
from flask import Flask, request, render_template_string, send_file

from scraper import get_video_urls
from utils import save_records_to_json

APP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUT_FILE = os.path.join(DATA_DIR, "extracted.json")

app = Flask(__name__)

INDEX_HTML = '''
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>YouTube Recipe Extractor</title>
    <style>
      body { font-family: system-ui, -apple-system, Arial, sans-serif; padding: 24px }
      .thumb { width:140px; border-radius:8px }
      .row { display:flex; gap:12px; align-items:center; margin-bottom:12px }
      .card { border:1px solid #eee; padding:12px; border-radius:8px }
    </style>
  </head>
  <body>
    <h1>YouTube Recipe Extractor</h1>
    <form method="post" action="/extract">
      <label>YouTube channel or playlist URL:</label><br>
      <input type="text" name="channel" size="80" required>
      <button type="submit">Extract All Videos</button>
    </form>
    <p>Saved JSON: <a href="/download">Download</a></p>
  </body>
</html>
'''


RESULT_HTML = '''
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Extraction Results</title>
    <style>
      body { font-family: system-ui, -apple-system, Arial, sans-serif; padding:24px }
      .thumb { width:140px; border-radius:8px }
      .item { display:flex; gap:12px; align-items:center; margin-bottom:12px }
    </style>
  </head>
  <body>
    <h1>Extraction Results</h1>
    <p>Processed {{ count }} videos. Saved to {{ out_file }}</p>
    {% for r in results %}
      <div class="item">
        <a href="{{ r.youtubeVideoLink }}" target="_blank"><img class="thumb" src="{{ r.thumbnail }}"></a>
        <div>
          <div><a href="{{ r.youtubeVideoLink }}">{{ r.youtubeVideoLink }}</a></div>
          <div><small>{{ r.videoId }}</small></div>
        </div>
      </div>
    {% endfor %}
    <p><a href="/">Back</a> — <a href="/download">Download JSON</a></p>
  </body>
</html>
'''


@app.route('/', methods=['GET'])
def index():
    return render_template_string(INDEX_HTML)


@app.route('/extract', methods=['POST'])
def extract():
    channel = request.form.get('channel', '').strip()
    if not channel:
        return 'Please provide a YouTube channel URL', 400

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
    return render_template_string(RESULT_HTML, count=len(results), results=results, out_file=OUT_FILE)


@app.route('/download')
def download():
    if not os.path.exists(OUT_FILE):
        return 'No extraction file yet.', 404
    return send_file(OUT_FILE, as_attachment=True, download_name=os.path.basename(OUT_FILE))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
