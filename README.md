# Metadata Stripper

Local CLI tools to erase all embedded metadata from video, image, and PDF files — GPS location, timestamps, camera model, author info, and any other identifying information — before sharing them.

Output files are always saved to your `~/Downloads` folder with a `_clean` suffix. Original files are never touched.

---

## Requirements

### macOS

- Python 3
- [ffmpeg](https://ffmpeg.org/) — for video stripping

```bash
brew install ffmpeg
```

- [Pillow](https://python-pillow.org/) — for image stripping
- [pypdf](https://pypdf.readthedocs.io/) — for PDF stripping

```bash
pip3 install Pillow pikepdf --break-system-packages
```

---

### Tails OS

Python 3 is pre-installed on Tails. Follow these steps exactly to ensure identical behavior to the tested version.

**1. Open a terminal** (Applications → System Tools → Terminal)

**2. Install ffmpeg:**
```bash
sudo apt-get install -y ffmpeg
```
When prompted, enter your administration password (set at Tails startup).

**3. Install exact Python package versions:**
```bash
pip3 install "Pillow==12.1.0" "pikepdf==10.5.1"
```

> **Why pin versions?** Older versions of pikepdf (below 8.x) and Pillow (below 10.x) may leave behind `Creator`, `ModifyDate`, or `Producer` fields even after stripping. Using these exact versions guarantees the same behavior as tested.

If pip cannot reach the internet, use the Tor proxy:
```bash
pip3 install --proxy socks5h://127.0.0.1:9050 "Pillow==12.1.0" "pikepdf==10.5.1"
```

Or install via apt as a fallback (may be an older version — less reliable):
```bash
sudo apt-get install -y python3-pikepdf python3-pil
```

**4. Copy the scripts** into your Persistent Storage so they survive reboots:
```bash
cp strip.py strip_image.py strip_pdf.py strip_to_mp3.py ~/Persistent/
```

Then run from there:
```bash
python3 ~/Persistent/strip.py /path/to/video.mp4
python3 ~/Persistent/strip_image.py /path/to/photo.jpg
python3 ~/Persistent/strip_pdf.py /path/to/document.pdf
```

> **Important:** Installed packages are **not persisted** across Tails sessions by default. You will need to reinstall them each session unless you configure [Additional Software](https://tails.boum.org/doc/persistent_storage/additional_software/) in Persistent Storage settings.

**Output on Tails:** files are saved to `~/Downloads` which maps to `/home/amnesia/Downloads/`.

---

## Usage

### Videos

```bash
python3 strip.py <video_file>
python3 strip.py <video_file> --compress
python3 strip.py <video_file> -o /path/to/output.mp4
```

| Flag | Description |
|------|-------------|
| `--compress` | Re-encode with H.264 to reduce file size (takes longer) |
| `-o`, `--output` | Custom output path (overrides the default Downloads destination) |

**Examples:**
```bash
python3 strip.py ~/Movies/clip.mp4
python3 strip.py ~/Movies/clip.mp4 --compress
```

**Supported formats:** any format supported by ffmpeg (mp4, mov, mkv, avi, etc.)

---

### PDFs

```bash
python3 strip_pdf.py <pdf_file>
python3 strip_pdf.py <pdf_file> -o /path/to/output.pdf
```

| Flag | Description |
|------|-------------|
| `-o`, `--output` | Custom output path (overrides the default Downloads destination) |

**Examples:**
```bash
python3 strip_pdf.py ~/Documents/contract.pdf
```

Removes: author, creator, producer, creation date, modification date, keywords, subject, and any other embedded metadata fields.

---

### Images

```bash
python3 strip_image.py <image_file>
python3 strip_image.py <image_file> --compress
python3 strip_image.py <image_file> -o /path/to/output.jpg
```

| Flag | Description |
|------|-------------|
| `--compress` | Save at lower quality/higher compression to reduce file size |
| `-o`, `--output` | Custom output path (overrides the default Downloads destination) |

**Examples:**
```bash
python3 strip_image.py ~/Pictures/photo.jpg
python3 strip_image.py ~/Pictures/photo.jpg --compress
```

**Supported formats:** jpg, jpeg, png, webp, tiff, bmp

---

## What gets removed

| Data | Videos | Images | PDFs |
|------|--------|--------|------|
| GPS / location | yes | yes | yes |
| Date & time recorded | yes | yes | yes |
| Camera / device model | yes | yes | - |
| Device serial number | yes | yes | - |
| Author / creator name | - | - | yes |
| Software / encoder info | yes | yes | yes |
| Keywords / subject | - | - | yes |

> **Note:** Filesystem timestamps (created/modified dates shown by your OS) are assigned locally by each machine and are **not embedded** in the file — they do not travel with the file when you share it.

---

## Verifying the result

**Videos:**
```bash
ffprobe -v quiet -print_format json -show_format output_clean.mp4
```
The `tags` field should be empty or contain only container format identifiers (`major_brand`, etc.).

**Images:**
```bash
python3 -c "from PIL import Image; from PIL.ExifTags import TAGS; img = Image.open('output_clean.jpg'); print(img.getexif())"
```
Should print `{}`.

**PDFs:**
```bash
python3 -c "from pypdf import PdfReader; r = PdfReader('output_clean.pdf'); print(r.metadata)"
```
Should print `{}`.
