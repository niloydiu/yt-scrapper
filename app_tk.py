"""
app_tk.py

Tkinter GUI alternative for environments where PyQt6 fails to run.
Provides the same functionality: input fields for channel URL and output JSON,
Start/Stop buttons, progress bar, and a status log. Runs scraping and parsing
in a background thread and updates the UI via a queue.
"""
import threading
import queue
import time
import traceback
from urllib.parse import urlparse, parse_qs

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from scraper import get_video_metadata
from transcripts import fetch_transcript_and_translation
from parser import extract_ingredients
from utils import save_records_to_json


class WorkerThread(threading.Thread):
    def __init__(self, channel_url, out_file, update_queue):
        super().__init__()
        self.channel_url = channel_url
        self.out_file = out_file
        self.update_queue = update_queue
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        try:
            self.update_queue.put(("status", "Extracting video metadata..."))
            videos = get_video_metadata(self.channel_url)
            total = len(videos)
            self.update_queue.put(("status", f"Found {total} videos"))
            results = []

            for idx, video in enumerate(videos, start=1):
                if self.stopped():
                    break
                
                vurl = video['youtubeVideoLink']
                vid = video['videoId']
                self.update_queue.put(("status", f"Processing ({idx}/{total}): {video['title']}"))

                try:
                    transcript_text, translation_text = fetch_transcript_and_translation(vid)
                except Exception as e:
                    self.update_queue.put(("status", f"No transcript for {vid}: {e}"))
                    transcript_text = ""
                    translation_text = ""

                ingredients = extract_ingredients(translation_text or transcript_text)

                video.update({
                    "id": idx,
                    "transcript": transcript_text,
                    "translation": translation_text,
                    "ingredients": ingredients,
                })
                results.append(video)

                try:
                    save_records_to_json(results, self.out_file)
                except Exception as e:
                    self.update_queue.put(("status", f"Failed saving JSON so far: {e}"))

                percent = int((idx / total) * 100) if total else 0
                self.update_queue.put(("progress", percent))

            self.update_queue.put(("status", "Finished processing videos."))
            self.update_queue.put(("progress", 100))
            self.update_queue.put(("done", True))

        except Exception as e:
            tb = traceback.format_exc()
            self.update_queue.put(("status", f"Worker error: {e}\n{tb}"))
            self.update_queue.put(("done", True))


class App:
    def __init__(self, root):
        self.root = root
        root.title("YouTube Recipe Ingredient Extractor (Tk)")
        root.geometry("800x500")

        frm = ttk.Frame(root, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="YouTube Channel URL:").pack(anchor=tk.W)
        self.channel_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.channel_var).pack(fill=tk.X)

        file_row = ttk.Frame(frm)
        file_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(file_row, text="Output JSON filename:").pack(side=tk.LEFT)
        self.file_var = tk.StringVar(value="data.json")
        ttk.Entry(file_row, textvariable=self.file_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))
        ttk.Button(file_row, text="Browse", command=self.browse_file).pack(side=tk.LEFT)

        btn_row = ttk.Frame(frm)
        btn_row.pack(fill=tk.X, pady=(10, 0))
        self.start_btn = ttk.Button(btn_row, text="Start", command=self.start)
        self.start_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(btn_row, text="Stop", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.progress = ttk.Progressbar(frm, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(frm, text="Status Log:").pack(anchor=tk.W, pady=(8, 0))
        self.log = tk.Text(frm, height=15)
        self.log.pack(fill=tk.BOTH, expand=True)

        self.update_queue = queue.Queue()
        self.worker = None
        self.root.after(200, self.process_queue)

    def browse_file(self):
        filename = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON files', '*.json'), ('All files', '*.*')], initialfile=self.file_var.get())
        if filename:
            self.file_var.set(filename)

    def append_log(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def start(self):
        channel = self.channel_var.get().strip()
        out_file = self.file_var.get().strip() or 'data.json'
        if not channel:
            messagebox.showwarning('Missing input', 'Please provide a YouTube channel URL')
            return

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress['value'] = 0
        self.log.delete('1.0', tk.END)

        self.worker = WorkerThread(channel, out_file, self.update_queue)
        self.worker.start()

    def stop(self):
        if self.worker:
            self.worker.stop()
            self.append_log('Stopping worker...')
            self.stop_btn.config(state=tk.DISABLED)

    def process_queue(self):
        try:
            while True:
                item = self.update_queue.get_nowait()
                kind, val = item
                if kind == 'status':
                    self.append_log(val)
                elif kind == 'progress':
                    try:
                        self.progress['value'] = int(val)
                    except Exception:
                        pass
                elif kind == 'done':
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        finally:
            self.root.after(200, self.process_queue)


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
