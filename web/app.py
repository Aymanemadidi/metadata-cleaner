import os
import shutil
import sys
import tempfile
import threading
import time
import zipfile

from flask import Flask, after_this_request, render_template, request, send_file

# Allow imports from the parent directory (strip_image, strip_pdf, strip)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strip import strip_video
from strip_image import strip_image, strip_jpeg_lossless
from strip_pdf import strip_pdf

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".flv", ".wmv", ".m4v"}
PDF_EXTS = {".pdf"}
ALL_SUPPORTED = IMAGE_EXTS | VIDEO_EXTS | PDF_EXTS


def detect_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in PDF_EXTS:
        return "pdf"
    return None


def process_file(input_path, output_path, file_type, compress):
    if file_type == "image":
        strip_image(input_path, output_path, compress=compress)
    elif file_type == "video":
        strip_video(input_path, output_path, compress=compress)
    elif file_type == "pdf":
        strip_pdf(input_path, output_path)


def cleanup_later(path, delay=5.0):
    def _clean():
        time.sleep(delay)
        shutil.rmtree(path, ignore_errors=True)
    threading.Thread(target=_clean, daemon=True).start()


def sweep_old_temps():
    while True:
        time.sleep(300)
        cutoff = time.time() - 600
        tmp_base = tempfile.gettempdir()
        try:
            for entry in os.scandir(tmp_base):
                if entry.name.startswith("metastrip_") and entry.is_dir():
                    if entry.stat().st_mtime < cutoff:
                        shutil.rmtree(entry.path, ignore_errors=True)
        except Exception:
            pass


threading.Thread(target=sweep_old_temps, daemon=True).start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        return render_template("index.html", error="No files selected."), 400

    compress = request.form.get("compress") == "1"
    tmpdir = tempfile.mkdtemp(prefix="metastrip_")
    outputs = []
    errors = []

    for f in files:
        if not f.filename:
            continue
        file_type = detect_type(f.filename)
        if not file_type:
            errors.append(f"{f.filename}: unsupported format")
            continue

        name, ext = os.path.splitext(f.filename)
        input_path = os.path.join(tmpdir, f"input_{f.filename}")
        output_path = os.path.join(tmpdir, f"{name}_clean{ext}")
        f.save(input_path)

        try:
            process_file(input_path, output_path, file_type, compress)
            outputs.append((f"{name}_clean{ext}", output_path))
        except Exception as e:
            errors.append(f"{f.filename}: {e}")

    if not outputs:
        shutil.rmtree(tmpdir, ignore_errors=True)
        error_msg = "Processing failed. " + "; ".join(errors) if errors else "No supported files."
        return render_template("index.html", error=error_msg), 400

    @after_this_request
    def cleanup(response):
        cleanup_later(tmpdir)
        return response

    if len(outputs) == 1:
        download_name, path = outputs[0]
        return send_file(path, as_attachment=True, download_name=download_name)

    zip_path = os.path.join(tmpdir, "cleaned_files.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for download_name, path in outputs:
            zf.write(path, download_name)

    return send_file(zip_path, as_attachment=True, download_name="cleaned_files.zip")


if __name__ == "__main__":
    app.run(port=5000)
