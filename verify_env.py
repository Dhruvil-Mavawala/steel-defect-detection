"""
verify_env.py — Environment health check for Steel Defect Detection Pro.
Run INSIDE the venv:  python verify_env.py
"""
import sys

OK   = "  ✅"
FAIL = "  ❌"
WARN = "  ⚠️ "

# ── Python version ────────────────────────────────────────────────────────────
print("\n── Python ──────────────────────────────────────────────────────")
v = sys.version_info
icon = OK if (v.major, v.minor) == (3, 10) else WARN
print(f"{icon} Python {v.major}.{v.minor}.{v.micro}  (3.10.x recommended)")


# ── Check helper ─────────────────────────────────────────────────────────────
def check(label: str, fn) -> bool:
    try:
        msg = fn()
        print(f"{OK} {label}: {msg}")
        return True
    except Exception as e:
        print(f"{FAIL} {label}: {e}")
        return False


# ── Package checks ────────────────────────────────────────────────────────────
print("\n── Packages ────────────────────────────────────────────────────")

def chk_numpy():
    import numpy as np
    major, minor = (int(x) for x in np.__version__.split(".")[:2])
    if (major, minor) >= (2, 0):
        raise RuntimeError(
            f"numpy {np.__version__} >= 2.0 breaks torch. "
            "Run: pip install numpy==1.26.4"
        )
    return np.__version__

def chk_torch():
    import torch
    import torch.nn                 # verify nn submodule
    import torch._prims_common      # catches partial/corrupt installs
    return torch.__version__

def chk_torchvision():
    import torchvision
    return torchvision.__version__

def chk_cv2():
    import cv2, numpy as np
    img  = np.zeros((64, 64, 3), dtype=np.uint8)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    assert gray.shape == (64, 64), "cvtColor shape mismatch"
    return cv2.__version__

def chk_pil():
    from PIL import Image
    img = Image.new("RGB", (32, 32), (255, 0, 0))
    assert img.size == (32, 32)
    import PIL
    return PIL.__version__

def chk_ultralytics():
    import ultralytics
    return ultralytics.__version__

def chk_streamlit():
    import streamlit
    return streamlit.__version__

def chk_plotly():
    import plotly
    return plotly.__version__

def chk_pandas():
    import pandas as pd
    return pd.__version__

def chk_firebase():
    import firebase_admin
    return firebase_admin.__version__

checks = [
    ("numpy",                 chk_numpy),
    ("torch",                 chk_torch),
    ("torchvision",           chk_torchvision),
    ("opencv-headless (cv2)", chk_cv2),
    ("Pillow",                chk_pil),
    ("ultralytics",           chk_ultralytics),
    ("streamlit",             chk_streamlit),
    ("plotly",                chk_plotly),
    ("pandas",                chk_pandas),
    ("firebase-admin",        chk_firebase),
]

results = [check(lbl, fn) for lbl, fn in checks]

# ── torch ↔ numpy bridge ──────────────────────────────────────────────────────
print("\n── torch ↔ numpy bridge ────────────────────────────────────────")

def chk_torch_numpy():
    import torch, numpy as np
    arr  = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    t    = torch.from_numpy(arr)
    back = t.numpy()
    assert back.sum() == 6.0, "round-trip sum mismatch"
    return "torch.from_numpy ↔ .numpy() OK"

check("torch ↔ numpy", chk_torch_numpy)

# ── PIL → tensor (tobytes path used in utils.py) ──────────────────────────────
print("\n── PIL → tensor (tobytes path) ─────────────────────────────────")

def chk_pil_tensor():
    import torch
    from PIL import Image
    img = Image.new("RGB", (224, 224), (128, 64, 32))
    raw = img.tobytes()
    t   = torch.frombuffer(bytearray(raw), dtype=torch.uint8)
    t   = t.reshape(224, 224, 3).permute(2, 0, 1).float() / 255.0
    x   = t.unsqueeze(0)
    assert x.shape == (1, 3, 224, 224), f"unexpected shape {x.shape}"
    assert 0.0 <= x.min().item() <= x.max().item() <= 1.0, "values out of [0,1]"
    return f"shape {tuple(x.shape)}, range [{x.min():.3f}, {x.max():.3f}]"

check("PIL → tensor", chk_pil_tensor)

# ── Mini inference (no weights needed) ───────────────────────────────────────
print("\n── Mini inference ──────────────────────────────────────────────")

def chk_inference():
    import torch, torch.nn as nn
    from PIL import Image

    model = nn.Sequential(
        nn.Conv2d(3, 8, 3, padding=1),
        nn.ReLU(),
        nn.AdaptiveAvgPool2d(1),
        nn.Flatten(),
        nn.Linear(8, 2),
    ).eval()

    img = Image.new("RGB", (224, 224), (100, 150, 200))
    raw = img.tobytes()
    t   = torch.frombuffer(bytearray(raw), dtype=torch.uint8)
    t   = t.reshape(224, 224, 3).permute(2, 0, 1).float() / 255.0

    with torch.no_grad():
        out = model(t.unsqueeze(0))

    assert out.shape == (1, 2), f"unexpected output shape {out.shape}"
    return f"output {tuple(out.shape)} — OK"

check("mini inference", chk_inference)

# ── cv2 + numpy interop ───────────────────────────────────────────────────────
print("\n── cv2 + numpy interop ─────────────────────────────────────────")

def chk_cv2_numpy():
    import cv2, numpy as np
    from PIL import Image

    # Simulate the exact path in utils.py
    pil_img  = Image.new("RGB", (200, 200), (180, 90, 30))
    img_rgb  = np.asarray(pil_img, dtype=np.uint8).copy()
    img_bgr  = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    hsv      = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    mask     = cv2.inRange(hsv,
                           np.array([5,  50,  50], dtype=np.uint8),
                           np.array([25, 255, 255], dtype=np.uint8))
    kernel   = np.ones((5, 5), np.uint8)
    mask     = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    mask     = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return f"pipeline OK — {len(contours)} contour(s) found"

check("cv2 + numpy pipeline", chk_cv2_numpy)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n────────────────────────────────────────────────────────────────")
passed = sum(results)
total  = len(results)

if passed == total:
    print(f"✅  All {total}/10 package checks passed — environment is production-ready.")
    print("    Run:  streamlit run app.py\n")
else:
    failed = total - passed
    print(f"❌  {failed}/{total} checks failed — fix the issues above.")
    print("\n    Quick fix:")
    print("      1. Double-check you are inside the venv  (venv\\Scripts\\activate)")
    print("      2. Run:  pip install -r requirements.txt")
    print("      3. Re-run this script\n")
    sys.exit(1)
