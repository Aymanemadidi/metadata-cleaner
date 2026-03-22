# Metadata Stripper

Local CLI tools to erase all embedded metadata from video and image files — GPS location, timestamps, camera model, and any other identifying information — before sharing them.

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

```bash
pip3 install Pillow --break-system-packages
```

---

### Tails OS

Python 3 is pre-installed on Tails. You only need to install ffmpeg and Pillow.

**1. Open a terminal** (Applications → System Tools → Terminal)

**2. Install ffmpeg:**
```bash
sudo apt-get install -y ffmpeg
```
When prompted, enter your administration password (set at Tails startup).

**3. Install Pillow:**
```bash
pip3 install Pillow
```

**4. Clone or copy the scripts** into your Persistent Storage so they survive reboots:
```bash
# If you have Persistent Storage enabled (recommended):
cp strip.py strip_image.py ~/Persistent/

# Then run from there:
python3 ~/Persistent/strip.py /path/to/video.mp4
python3 ~/Persistent/strip_image.py /path/to/photo.jpg
```

> **Important:** ffmpeg and Pillow are **not persisted** across Tails sessions by default. You will need to reinstall them each session unless you configure [Additional Software](https://tails.boum.org/doc/persistent_storage/additional_software/) in Persistent Storage settings.
>
> To persist them automatically on every boot, add `ffmpeg` via the Additional Software feature in Tails, and add `Pillow` to a `requirements.txt` that you install on startup.

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

| Data | Videos | Images |
|------|--------|--------|
| GPS / location | yes | yes |
| Date & time recorded | yes | yes |
| Camera model & manufacturer | yes | yes |
| Device serial number | yes | yes |
| Software / encoder info | yes | yes |

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
