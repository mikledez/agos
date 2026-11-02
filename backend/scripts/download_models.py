#!/usr/bin/env python3
import sys
import zipfile
import tempfile
from pathlib import Path
try:
    import urllib.request
except ImportError:
    print("urllib not available", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://huggingface.co/Tau-J/RTMPose/resolve/main/rtmposev1/onnx_sdk"
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
FILES = [
    ("yolox_nano_8xb8-300e_humanart-40f6f0d0.zip", "yolox-nano_person.onnx"),
    ("rtmpose-m_simcc-body7_pt-body7-halpe26_700e-256x192-4d3e73dd_20230605.zip", "rtmpose-m_halpe26.onnx"),
]

def download(url, dest):
    print(f"Downloading {url} -> {dest}")
    for attempt in range(3):
        try:
            urllib.request.urlretrieve(url, dest)
            return
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Retry {attempt+1}/3: {e}", file=sys.stderr)

def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading ONNX models into {MODEL_DIR}")
    for zip_name, out_name in FILES:
        if (MODEL_DIR / out_name).exists():
            print(f"Already present: {out_name}")
            continue
        url = f"{BASE_URL}/{zip_name}"
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / zip_name
            download(url, str(zip_path))
            with zipfile.ZipFile(zip_path) as z:
                member = next((m for m in z.namelist() if m.endswith("end2end.onnx")), None)
                if not member:
                    print(f"No end2end.onnx in {zip_name}", file=sys.stderr)
                    sys.exit(1)
                data = z.read(member)
                (MODEL_DIR / out_name).write_bytes(data)
                print(f"Wrote {out_name}")
    print("Done.")
    for p in MODEL_DIR.iterdir():
        print(p)

if __name__ == "__main__":
    main()
