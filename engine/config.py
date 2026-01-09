import os
from pathlib import Path
import os

HF_STORE = "./hfstore"

os.environ["HF_HOME"] = HF_STORE
os.environ["HUGGINGFACE_HUB_CACHE"] = HF_STORE
os.environ["TRANSFORMERS_CACHE"] = HF_STORE
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# ======================================================
# PROJECT ROOT (auto-detected)
# ======================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ======================================================
# STORAGE PATHS
# ======================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

HF_STORE = PROJECT_ROOT / "hfstore"
REF_DIR  = PROJECT_ROOT / "ref"
OUT_DIR  = PROJECT_ROOT / "outputs" / "temp" / "audio"

os.environ["HF_HOME"] = str(HF_STORE)
os.environ["HUGGINGFACE_HUB_CACHE"] = str(HF_STORE)
os.environ["TRANSFORMERS_CACHE"] = str(HF_STORE)
os.environ["HF_DATASETS_CACHE"] = str(HF_STORE)

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"


# ======================================================
# ENSURE FOLDERS EXIST
# ======================================================

HF_STORE.mkdir(parents=True, exist_ok=True)
REF_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)
