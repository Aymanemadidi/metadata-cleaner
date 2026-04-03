#!/bin/bash
# Setup script for Metadata Stripper on Tails OS
# Run once after cloning the repo: bash setup_tails.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }

echo ""
echo "================================="
echo "  Metadata Stripper — Tails Setup"
echo "================================="
echo ""

# ── 1. Check we're running on Tails ──────────────────────────────────────────
if ! grep -qi "tails" /etc/os-release 2>/dev/null; then
    warn "This script is designed for Tails OS. Proceeding anyway..."
fi

# ── 2. Check Python 3 ────────────────────────────────────────────────────────
echo "Checking Python 3..."
if ! command -v python3 &>/dev/null; then
    fail "Python 3 not found. Install it with: sudo apt-get install -y python3"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
ok "$PYTHON_VERSION"

# ── 3. Install ffmpeg ─────────────────────────────────────────────────────────
echo ""
echo "Installing ffmpeg..."
if command -v ffmpeg &>/dev/null; then
    ok "ffmpeg already installed: $(ffmpeg -version 2>&1 | head -1)"
else
    sudo apt-get install -y ffmpeg
    if command -v ffmpeg &>/dev/null; then
        ok "ffmpeg installed: $(ffmpeg -version 2>&1 | head -1)"
    else
        fail "ffmpeg installation failed"
        exit 1
    fi
fi

# ── 4. Install Python packages with pinned versions ───────────────────────────
echo ""
echo "Installing Python packages (pinned versions)..."

install_pkg() {
    local pkg=$1
    local version=$2
    echo "  Installing ${pkg}==${version}..."
    if pip3 install "${pkg}==${version}" --quiet 2>/dev/null; then
        ok "${pkg}==${version}"
    elif pip3 install "${pkg}==${version}" --break-system-packages --quiet 2>/dev/null; then
        ok "${pkg}==${version}"
    else
        warn "Direct install failed, trying via Tor proxy..."
        if pip3 install --proxy socks5h://127.0.0.1:9050 "${pkg}==${version}" --quiet 2>/dev/null; then
            ok "${pkg}==${version} (via Tor)"
        elif pip3 install --proxy socks5h://127.0.0.1:9050 "${pkg}==${version}" --break-system-packages --quiet 2>/dev/null; then
            ok "${pkg}==${version} (via Tor)"
        else
            fail "Could not install ${pkg}. Check your network connection."
            exit 1
        fi
    fi
}

install_pkg "Pillow" "12.1.0"
install_pkg "pikepdf" "10.5.1"

# ── 5. Verify imports ─────────────────────────────────────────────────────────
echo ""
echo "Verifying package imports..."

python3 -c "from PIL import Image; print('  Pillow OK')" || { fail "Pillow import failed"; exit 1; }
ok "Pillow import"

python3 -c "import pikepdf; print('  pikepdf OK')" || { fail "pikepdf import failed"; exit 1; }
ok "pikepdf import"

# ── 6. Verify scripts exist ───────────────────────────────────────────────────
echo ""
echo "Checking scripts..."

SCRIPTS="strip.py strip_image.py strip_pdf.py strip_to_mp3.py"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for script in $SCRIPTS; do
    if [ -f "${SCRIPT_DIR}/${script}" ]; then
        ok "${script}"
    else
        fail "${script} not found in ${SCRIPT_DIR}"
        exit 1
    fi
done

# ── 7. Verify ffprobe works ───────────────────────────────────────────────────
echo ""
echo "Checking ffprobe..."
if command -v ffprobe &>/dev/null; then
    ok "ffprobe available"
else
    fail "ffprobe not found (should come with ffmpeg)"
    exit 1
fi

# ── 8. Run a quick functional test ───────────────────────────────────────────
echo ""
echo "Running functional tests..."

# Test image strip
python3 -c "
import os, sys, tempfile, struct
sys.path.insert(0, '${SCRIPT_DIR}')
from strip_image import strip_jpeg_lossless
from PIL import Image

# Create a minimal JPEG with fake EXIF (APP1 segment)
# SOI + APP1 (fake exif) + APP0 (JFIF) + minimal SOF/SOS
test_jpg = bytes([
    0xff, 0xd8,                          # SOI
    0xff, 0xe1, 0x00, 0x08,             # APP1 marker + length 8
    0x45, 0x78, 0x69, 0x66, 0x00, 0x00, # 'Exif\0\0'
    0xff, 0xda, 0x00, 0x08,             # SOS marker (rest is image data)
    0x01, 0x01, 0x00, 0x00, 0x3f, 0x00,
    0xff, 0xd9                           # EOI
])

with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
    f.write(test_jpg)
    tmp_in = f.name

with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
    tmp_out = f.name

try:
    strip_jpeg_lossless(tmp_in, tmp_out)
    with open(tmp_out, 'rb') as f:
        result = f.read()
    # APP1 segment should be gone
    assert b'\xff\xe1' not in result, 'EXIF segment still present!'
    print('  Image strip: PASSED')
finally:
    os.unlink(tmp_in)
    os.unlink(tmp_out)
" && ok "Image strip test" || { fail "Image strip test failed"; exit 1; }

# Test PDF strip
python3 -c "
import sys, tempfile, os
sys.path.insert(0, '${SCRIPT_DIR}')
import pikepdf
from pikepdf import Dictionary, String

# Create a minimal PDF with metadata
with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
    tmp_in = f.name
with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
    tmp_out = f.name

try:
    pdf = pikepdf.new()
    pdf.trailer['/Info'] = Dictionary(
        Creator=String('Microsoft Word'),
        ModDate=String('D:20260320142211'),
        Author=String('John Doe'),
    )
    with pdf.open_metadata() as meta:
        meta['xmp:CreatorTool'] = 'Microsoft Word'
        meta['xmp:ModifyDate'] = '2026-03-20T14:22:11'
    pdf.save(tmp_in)

    # Run strip
    with pikepdf.open(tmp_in) as p:
        if '/Info' in p.trailer:
            del p.trailer['/Info']
        try:
            with p.open_metadata(set_pikepdf_as_editor=False) as m:
                for k in list(m.keys()): del m[k]
        except: pass
        if '/Metadata' in p.Root:
            del p.Root['/Metadata']
        p.save(tmp_out, fix_metadata_version=False)

    with pikepdf.open(tmp_out) as p:
        docinfo = dict(p.docinfo)
        try:
            with p.open_metadata(set_pikepdf_as_editor=False) as m:
                xmp = dict(m)
        except:
            xmp = {}
    assert docinfo == {}, f'docinfo not empty: {docinfo}'
    assert xmp == {}, f'XMP not empty: {xmp}'
    print('  PDF strip: PASSED')
finally:
    os.unlink(tmp_in)
    os.unlink(tmp_out)
" && ok "PDF strip test" || { fail "PDF strip test failed"; exit 1; }

# ── 9. Summary ────────────────────────────────────────────────────────────────
echo ""
echo "================================="
ok "All checks passed. Ready to use."
echo "================================="
echo ""
echo "Usage:"
echo "  python3 ${SCRIPT_DIR}/strip.py <video>"
echo "  python3 ${SCRIPT_DIR}/strip_image.py <image>"
echo "  python3 ${SCRIPT_DIR}/strip_pdf.py <document.pdf>"
echo "  python3 ${SCRIPT_DIR}/strip_to_mp3.py <video>"
echo ""
echo "Output files are saved to ~/Downloads"
echo ""
