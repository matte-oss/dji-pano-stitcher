import argparse
import shutil
import subprocess
import sys
import platform
import urllib.request
import zipfile
import tarfile
from pathlib import Path

# ---------------- CONFIG ----------------
SKYFILL_URLS = {
    "Windows": "https://stuvelfoto.nl/downloads/skyfill/skyfill-v1.6-windows.zip",
    "Linux": "https://stuvelfoto.nl/downloads/skyfill/skyfill-v1.6-linux.tar.gz",
}
EXIFTOOL_URL = "https://sourceforge.net/projects/exiftool/files/exiftool-13.45_64.zip/download"
HUGIN_BIN = Path(r"C:\Program Files\Hugin\bin") if platform.system() == "Windows" else None

TOOLS_DIR = Path("tools")
TEMP_DIR = Path("temp")
OUTPUT_DIR = Path("output")

# ---------------- UTILS ----------------
def fail(msg):
    print(f"\n❌ {msg}")
    sys.exit(1)

def find_tool(name):
    """Find tool in Hugin bin directory first, then in PATH"""
    if HUGIN_BIN and HUGIN_BIN.exists():
        tool_path = HUGIN_BIN / (name + ".exe" if platform.system() == "Windows" else name)
        if tool_path.exists():
            return str(tool_path)
    # Fall back to PATH
    found = shutil.which(name)
    if found:
        return found
    fail(f"Tool '{name}' not found in Hugin directory or PATH")

def run(cmd):
    print("▶", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)

# ---------------- STEP 1 ----------------
parser = argparse.ArgumentParser()
parser.add_argument("images", help="Folder containing DJI images")
parser.add_argument("--debug-skip", action="store_true", help="Skip stitching if temp files exist")
args = parser.parse_args()

image_dir = Path(args.images)
if not image_dir.is_dir():
    fail("Image folder does not exist")

# ---------------- STEP 2 ----------------
print("🔍 Locating required tools...")
TOOLS = {
    "pto_gen": find_tool("pto_gen"),
    "cpfind": find_tool("cpfind"),
    "autooptimiser": find_tool("autooptimiser"),
    "pano_modify": find_tool("pano_modify"),
    "nona": find_tool("nona"),
    "enblend": find_tool("enblend"),
    "magick": shutil.which("magick") or fail("ImageMagick not found in PATH"),
}
print("✅ Hugin and ImageMagick detected")

# ---------------- STEP 3: SKYFILL ----------------
def ensure_skyfill():
    system = platform.system()
    url = SKYFILL_URLS.get(system)
    if not url:
        fail(f"SkyFill not available for {system}")
    
    skyfill_dir = TOOLS_DIR / "skyfill"
    exe = skyfill_dir / ("skyfill.exe" if system == "Windows" else "skyfill")
    
    if exe.exists():
        return exe
    
    print("⬇ Downloading SkyFill...")
    skyfill_dir.mkdir(parents=True, exist_ok=True)
    archive = skyfill_dir / Path(url).name
    urllib.request.urlretrieve(url, archive)
    
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as z:
            z.extractall(skyfill_dir)
    else:
        with tarfile.open(archive) as t:
            t.extractall(skyfill_dir)
    
    archive.unlink()
    
    if not exe.exists():
        fail("SkyFill executable not found after extraction")
    
    if system != "Windows":
        exe.chmod(0o755)
    
    return exe

skyfill = ensure_skyfill()
print("✅ SkyFill ready")

# ---------------- STEP 3.5: EXIFTOOL ----------------
def ensure_exiftool():
    system = platform.system()
    exiftool_dir = TOOLS_DIR / "exiftool"
    
    if system == "Windows":
        exe = exiftool_dir / "exiftool.exe"
        if exe.exists():
            return exe
        
        print("⬇ Downloading ExifTool (this may take a while from SourceForge)...")
        exiftool_dir.mkdir(parents=True, exist_ok=True)
        archive = exiftool_dir / "exiftool.zip"
        
        # Download with progress indication
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(downloaded * 100 / total_size, 100)
                print(f"\r   Progress: {percent:.1f}%", end='', flush=True)
        
        urllib.request.urlretrieve(EXIFTOOL_URL, archive, show_progress)
        print()  # New line after progress
        
        print("📦 Extracting ExifTool...")
        with zipfile.ZipFile(archive) as z:
            z.extractall(exiftool_dir)
        archive.unlink()
        
        # Find the exe - it might be in a subdirectory
        temp_exe = exiftool_dir / "exiftool(-k).exe"
        if temp_exe.exists():
            temp_exe.rename(exe)
        elif not exe.exists():
            # Search recursively for any .exe file
            exes = list(exiftool_dir.rglob("*.exe"))
            if exes:
                # Move all contents from subdirectory to exiftool_dir root
                subdir = exes[0].parent
                for item in subdir.iterdir():
                    dest = exiftool_dir / item.name
                    item.rename(dest)
                    if dest.is_file() and dest.name == "exiftool(-k).exe":
                        dest.rename(exe)
                # Remove the now-empty subdirectory
                subdir.rmdir()
            else:
                fail("ExifTool executable not found after extraction")
        
        return exe
    else:
        # On Linux, check if exiftool is available
        found = shutil.which("exiftool")
        if found:
            return found
        fail("ExifTool not found. Please install it using your package manager (e.g., 'sudo apt install libimage-exiftool-perl')")

exiftool = ensure_exiftool()
print("✅ ExifTool ready")

# ---------------- STEP 4: STITCH ----------------
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

pto = TEMP_DIR / "pano.pto"
stitched = TEMP_DIR / "stitched.tif"

if args.debug_skip and stitched.exists():
    print("\n⏭️ Skipping stitching (temp files exist)")
else:
    print("\n📸 Creating panorama project...")
    run([TOOLS["pto_gen"], str(image_dir / "*"), "-o", pto])
    run([TOOLS["cpfind"], "--multirow", "-o", pto, pto])
    run([TOOLS["autooptimiser"], "-a", "-m", "-l", "-s", "-o", pto, pto])
    run([TOOLS["pano_modify"], "--canvas=AUTO", "-o", pto, pto])

    print("\n🔨 Stitching images...")
    run([TOOLS["nona"], "-o", TEMP_DIR / "pano", pto])
    run([TOOLS["enblend"], "-o", stitched, *TEMP_DIR.glob("pano*.tif")])

# ---------------- STEP 5: RESIZE ----------------
resized = TEMP_DIR / "resized.jpg"

if args.debug_skip and resized.exists():
    print("\n⏭️ Skipping resize (temp file exists)")
else:
    print("\n📐 Resizing to equirectangular format...")
    run([
        TOOLS["magick"], stitched,
        "-gravity", "south",
        "-background", "black",
        "-extent", "%[fx:max(w,h*2)]x%[fx:max(w/2,h)]",
        resized
    ])

# ---------------- STEP 6: SKYFILL ----------------
print("\n🌤️ Filling sky with SkyFill...")
final = OUTPUT_DIR / f"{image_dir.name}_pano.jpg"
# SkyFill outputs to same directory as input with -filled suffix
skyfill_output = resized.parent / f"{resized.stem}-filled.jpg"
run([
    str(skyfill),
    "-quality", "95",
    "-no-gpano-xmp",
    "-out", "jpeg",
    str(resized)
])
# Move the output to our desired location
if not skyfill_output.exists():
    fail(f"SkyFill did not create expected output file: {skyfill_output}")
skyfill_output.rename(final)

# ---------------- STEP 7: ADD EXIF DATA ----------------
print("\n📝 Adding panorama metadata...")
run([
    str(exiftool),
    "-UsePanoramaViewer=true",
    "-ProjectionType=equirectangular",
    "-overwrite_original",
    str(final)
])

# ---------------- STEP 8: CLEANUP ----------------
shutil.rmtree(TEMP_DIR)
print(f"\n🎉 Done → {final}")