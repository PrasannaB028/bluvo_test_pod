# engine/f5_engine.py

import os
import time
import torch
import numpy as np
import soundfile as sf
from pathlib import Path
from f5_tts.api import F5TTS

from .config import REF_DIR, OUT_DIR


class VoiceCloneEngine:
    def __init__(self, model_name="F5TTS_v1_Base"):
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # --------------------------------------------------
        # Resolve PROJECT ROOT safely
        # engine/f5_engine.py → engine → project root
        # --------------------------------------------------
        PROJECT_ROOT = Path(__file__).resolve().parents[1]

        HF_STORE = PROJECT_ROOT / "hfstore"

        VOCOS_ROOT = HF_STORE / "models--charactr--vocos-mel-24khz" / "snapshots"

        if not VOCOS_ROOT.exists():
            raise RuntimeError(
                f"❌ Vocos not found at {VOCOS_ROOT}\n"
                f"Check hfstore folder location."
            )

        # Pick first snapshot automatically
        snapshots = list(VOCOS_ROOT.iterdir())
        if not snapshots:
            raise RuntimeError("❌ No vocos snapshot found")

        VOCOS_PATH = snapshots[0]

        print(f"✅ Using local vocos at: {VOCOS_PATH}")

        # --------------------------------------------------
        # Initialize F5-TTS
        # --------------------------------------------------
        self.model = F5TTS(
            model=model_name,
            ckpt_file="",          # resolved from HF cache
            vocab_file="",         # internal default
            vocoder_local_path=str(VOCOS_PATH),
            hf_cache_dir=str(HF_STORE),
            device=device,
        )

        # --------------------------------------------------
        # Reference audio & text
        # --------------------------------------------------
        self.ref_audio = Path(REF_DIR) / "ref_audio.wav"
        self.ref_text = self._load_ref_text()

        if not self.ref_audio.exists():
            raise FileNotFoundError(f"Missing reference audio: {self.ref_audio}")

    def _load_ref_text(self):
        ref_text_file = Path(REF_DIR) / "ref_text.txt"
        if not ref_text_file.exists():
            raise FileNotFoundError("Missing ref_text.txt")
        return ref_text_file.read_text(encoding="utf8").strip()

    def synthesize(self, target_text: str) -> str:
        wav, sr, _ = self.model.infer(
            ref_file=str(self.ref_audio),
            ref_text=self.ref_text,
            gen_text=target_text.strip(),
            target_rms=0.14,
            cfg_strength=2.5,
            cross_fade_duration=0.18,
            nfe_step=36,
            speed=1.0,
        )

        if isinstance(wav, torch.Tensor):
            wav = wav.detach().cpu().numpy()
        if wav.ndim > 1:
            wav = wav[0]

        out_dir = Path(OUT_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)

        out_path = out_dir / f"f5_{int(time.time()*1000)}.wav"
        sf.write(out_path, wav, sr)

        return str(out_path)
