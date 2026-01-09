def normalize(text):
    return (
        text.upper()
        .replace(",", "")
        .replace(".", "")
        .replace("?", "")
        .replace("-", " ")
        .replace("|", " ")
        .replace("+", " ")
        .replace("—", " ")
        .strip()
    )


def tokenize(text):
    return normalize(text).split()


def merge_number_tokens(whisper_words):
    """
    Merge split numeric tokens like: 2 + 000 → 20000
    """
    merged = []
    i = 0

    while i < len(whisper_words):
        w = whisper_words[i]["word"]

        if (
            w.isdigit()
            and i + 1 < len(whisper_words)
            and whisper_words[i + 1]["word"].isdigit()
        ):
            merged.append({
                "word": w + whisper_words[i + 1]["word"],
                "start": whisper_words[i]["start"],
                "end": whisper_words[i + 1]["end"]
            })
            i += 2
        else:
            merged.append(whisper_words[i])
            i += 1

    return merged


def align_tts_to_whisper(tts_script, whisper_words):
    """
    Build mapping:
    TTS word index → Whisper word index
    """
    tts_words = tokenize(tts_script)
    whisper_stream = [w["word"] for w in whisper_words]

    mapping = {}
    wi = 0

    for ti, tw in enumerate(tts_words):
        while wi < len(whisper_stream):
            if whisper_stream[wi] == tw:
                mapping[ti] = wi
                wi += 1
                break
            wi += 1

    return tts_words, mapping


def extract_highlight_timestamps(
    highlight,
    tts_words,
    tts_to_whisper,
    whisper_words
):
    """
    Convert highlight phrase → (start, end) using alignment
    """
    h_words = tokenize(highlight)
    L = len(h_words)

    for i in range(len(tts_words) - L + 1):
        if tts_words[i:i + L] == h_words:
            ws = tts_to_whisper.get(i)
            we = tts_to_whisper.get(i + L - 1)

            if ws is not None and we is not None:
                return {
                    "text": highlight,
                    "start": whisper_words[ws]["start"],
                    "end": whisper_words[we]["end"]
                }

    return None
