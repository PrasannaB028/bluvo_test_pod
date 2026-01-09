import re
import json
from pathlib import Path
from faster_whisper import WhisperModel

# 🔒 GLOBAL WHISPER INSTANCE (LOAD ONCE PER WORKER)
_WHISPER_MODEL = None

# ======================================================
# NORMALIZATION
# ======================================================

def normalize(text: str) -> str:
    text = text.upper()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def tokenize(text: str):
    return normalize(text).split()

# ======================================================
# WORD COMPATIBILITY (STRICT + SAFE)
# ======================================================

def word_compatible(a: str, b: str) -> bool:
    if a == b:
        return True

    if a.replace(",", "") == b.replace(",", ""):
        return True

    if len(a) < 4 or len(b) < 4:
        return False

    return a.startswith(b[:4]) or b.startswith(a[:4])

# ======================================================
# MATCH THRESHOLD
# ======================================================

def match_threshold(word_count: int) -> float:
    if word_count <= 2:
        return 0.75
    if word_count <= 4:
        return 0.55
    return 0.35

# ======================================================
# PHRASE MATCHING (ANCHOR-BASED)
# ======================================================

def find_phrase_matches(words, h_words):
    H = len(h_words)
    threshold = match_threshold(H)
    matches = []

    for i in range(len(words)):
        if not word_compatible(h_words[0], words[i]["word"]):
            continue

        window = words[i:i + H + 3]
        matched = [words[i]]

        for hw in h_words[1:]:
            found = False
            for w in window:
                if word_compatible(hw, w["word"]):
                    matched.append(w)
                    found = True
                    break
            if not found:
                break

        ratio = len(matched) / H
        if ratio < threshold:
            continue

        start = matched[0]["start"]
        end = matched[-1]["end"]

        if end - start > max(2.5, H * 0.75):
            continue

        matches.append({
            "start": start,
            "end": end,
            "score": round(ratio, 2)
        })

    return matches

# ======================================================
# MAIN EXTRACTION (SERVERLESS SAFE)
# ======================================================

def extract_highlights(audio_path, highlights, debug_dir="debug"):
    global _WHISPER_MODEL

    Path(debug_dir).mkdir(exist_ok=True)

    # 🔥 LOAD WHISPER ONCE (NO RUNTIME DOWNLOADS)
    if _WHISPER_MODEL is None:
        _WHISPER_MODEL = WhisperModel(
            "small",                 # ✅ FAST + SERVERLESS SAFE
            device="cuda",
            compute_type="float16",
            download_root="/models/hf",
            local_files_only=True    # 🔒 ABSOLUTELY REQUIRED
        )

    model = _WHISPER_MODEL

    segments, _ = model.transcribe(
        audio_path,
        language="en",
        word_timestamps=True,
        vad_filter=True
    )

    # ------------------------------------------------------
    # Collect words + audio duration
    # ------------------------------------------------------
    words = []
    audio_end = 0.0

    for seg in segments:
        audio_end = max(audio_end, seg.end)
        for w in seg.words:
            words.append({
                "word": normalize(w.word),
                "start": round(w.start, 2),
                "end": round(w.end, 2)
            })

    matched = []
    unmatched = []

    debug = {
        "audio": audio_path,
        "audio_end": round(audio_end, 2),
        "matched": [],
        "gap_filled": []
    }

    # ------------------------------------------------------
    # PASS 1: Whisper matches
    # ------------------------------------------------------
    for idx, text in enumerate(highlights):
        h_words = tokenize(text)
        matches = find_phrase_matches(words, h_words)

        if matches:
            best = sorted(matches, key=lambda x: (-x["score"], x["start"]))[0]
            max_dur = max(1.2, len(h_words) * 0.7)

            start = best["start"]
            end = min(start + max_dur, best["end"], audio_end)

            if end > start:
                item = {
                    "index": idx,
                    "text": text,
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "score": best["score"],
                    "mode": "matched"
                }
                matched.append(item)
                debug["matched"].append(item)
            else:
                unmatched.append({"index": idx, "text": text})
        else:
            unmatched.append({"index": idx, "text": text})

    matched.sort(key=lambda x: x["start"])

    # ------------------------------------------------------
    # Build gaps
    # ------------------------------------------------------
    gaps = []

    if matched:
        if matched[0]["start"] > 0.3:
            gaps.append([0.0, matched[0]["start"]])

        for i in range(len(matched) - 1):
            gaps.append([matched[i]["end"], matched[i + 1]["start"]])

        if matched[-1]["end"] < audio_end:
            gaps.append([matched[-1]["end"], audio_end])
    else:
        gaps.append([0.0, audio_end])

    # ------------------------------------------------------
    # PASS 2: Gap fill
    # ------------------------------------------------------
    gap_idx = 0

    for u in unmatched:
        h_words = tokenize(u["text"])
        base_duration = max(1.0, len(h_words) * 0.6)

        while gap_idx < len(gaps):
            g_start, g_end = gaps[gap_idx]
            available = g_end - g_start

            if available >= 0.6:
                start = g_start + 0.2
                end = min(start + base_duration, audio_end)

                if end > start:
                    gaps[gap_idx][0] = end
                    item = {
                        "index": u["index"],
                        "text": u["text"],
                        "start": round(start, 2),
                        "end": round(end, 2),
                        "score": 0.0,
                        "mode": "gap_fill"
                    }
                    matched.append(item)
                    debug["gap_filled"].append(item)
                    break

            gap_idx += 1

    matched.sort(key=lambda x: x["index"])

    with open(Path(debug_dir) / f"{Path(audio_path).stem}_highlights.json", "w") as f:
        json.dump(debug, f, indent=2)

    return matched
