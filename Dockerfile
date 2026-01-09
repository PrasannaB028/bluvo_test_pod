FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

WORKDIR /app

# ------------------------------
# System dependencies
# ------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    python3 \
    python3-pip \
    libgl1 \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3 /usr/bin/python

# ------------------------------
# Python deps
# ------------------------------
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------
# HuggingFace cache
# ------------------------------
ENV HF_HOME=/models/hf
ENV HF_HUB_DISABLE_TELEMETRY=1
ENV HF_HUB_OFFLINE=0
RUN mkdir -p /models/hf

# ------------------------------
# Pre-download Whisper (CPU safe)
# ------------------------------
RUN python3 - <<EOF
from faster_whisper import WhisperModel
WhisperModel(
    "small",
    device="cpu",
    compute_type="int8",
    download_root="/models/hf"
)
EOF

# ------------------------------
# App code
# ------------------------------
COPY . .

CMD ["python3", "handler.py"]
