import json
from pathlib import Path
from datetime import datetime

REGISTRY_PATH = Path("data/voice_registry.json")
REGISTRY_PATH.parent.mkdir(exist_ok=True)

def load_registry():
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text())
    return {}

def save_registry(data):
    REGISTRY_PATH.write_text(json.dumps(data, indent=2))

def list_voices():
    return list(load_registry().keys())

def get_voice_id(name):
    return load_registry().get(name, {}).get("voice_id")

def add_voice(name, voice_id):
    data = load_registry()
    data[name] = {
        "voice_id": voice_id,
        "created_at": datetime.now().isoformat()
    }
    save_registry(data)
