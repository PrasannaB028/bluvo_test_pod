import os
import time
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

TMP_AUDIO_DIR = "/tmp/audio"

class ElevenLabsEngine:
    def __init__(self, voice_id):
        self.client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
        self.voice_id = voice_id

    def synthesize(self, text):
        os.makedirs(TMP_AUDIO_DIR, exist_ok=True)

        out = f"{TMP_AUDIO_DIR}/tts_{int(time.time()*1000)}.mp3"

        audio_stream = self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                use_speaker_boost=True
            )
        )

        with open(out, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)

        return out
