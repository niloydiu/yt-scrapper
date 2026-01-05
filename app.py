"""
app.py

PyQt6 GUI application that ties scraper, transcript fetching, parsing, and JSON
export together. Uses a worker thread so the UI stays responsive.
"""
import sys
import threading
import traceback
from urllib.parse import urlparse, parse_qs

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QProgressBar,
    QFileDialog,
)

from scraper import get_video_metadata
from transcripts import fetch_transcript_and_translation
from parser import extract_ingredients
from utils import save_records_to_json


class Worker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, channel_url, out_file):
        super().__init__()
        self.channel_url = channel_url
        self.out_file = out_file
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            self.status.emit("Extracting video metadata...")
            videos = get_video_metadata(self.channel_url)
            total = len(videos)
            self.status.emit(f"Found {total} videos")
            results = []

            for idx, video in enumerate(videos, start=1):
                if not self._is_running:
                    break

                vurl = video['youtubeVideoLink']
                vid = video['videoId']
                self.status.emit(f"Processing ({idx}/{total}): {video['title']}")

                try:
                    transcript_text, translation_text = fetch_transcript_and_translation(vid)
                except Exception as e:
                    self.status.emit(f"No transcript for {vid}: {str(e)}")
                    transcript_text = ""
                    translation_text = ""

                ingredients = extract_ingredients(translation_text or transcript_text)

                # Merge metadata with transcript/ingredients
                video.update({
                    "id": idx,
                    "transcript": transcript_text,
                    "translation": translation_text,
                    "ingredients": ingredients,
                })
                results.append(video)

                # write partial results each step
                try:
                    save_records_to_json(results, self.out_file)
                except Exception as e:
                    self.status.emit(f"Failed saving JSON so far: {e}")

                percent = int((idx / total) * 100)
                self.progress.emit(percent)

            self.status.emit("Finished processing videos.")
            self.progress.emit(100)
            self.finished.emit()

        except Exception as exc:
            self.status.emit(f"Worker error: {exc}")
            self.finished.emit()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Recipe Ingredient Extractor")
        self.resize(700, 450)

        self.channel_label = QLabel("YouTube Channel URL:")
        self.channel_input = QLineEdit()

        self.file_label = QLabel("Output JSON filename:")
        self.file_input = QLineEdit("data.json")
        self.file_browse = QPushButton("Browse")
        self.file_browse.clicked.connect(self.browse_file)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.channel_label)
        top_layout.addWidget(self.channel_input)

        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.file_browse)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_processing)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addLayout(file_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.progress)
        layout.addWidget(self.log)

        self.setLayout(layout)
        self.worker = None

    def browse_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Select output JSON file", "data.json", "JSON Files (*.json);;All Files (*)")
        if filename:
            self.file_input.setText(filename)

    def append_log(self, message):
        self.log.append(message)

    def start_processing(self):
        channel = self.channel_input.text().strip()
        out_file = self.file_input.text().strip() or "data.json"
        if not channel:
            self.append_log("Please provide a YouTube channel URL.")
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress.setValue(0)
        self.log.clear()

        self.worker = Worker(channel, out_file)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self.append_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def stop_processing(self):
        if self.worker:
            self.worker.stop()
            self.append_log("Stopping worker...")
            self.stop_btn.setEnabled(False)

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.append_log("Worker finished.")


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
