import json
from datetime import datetime

def log_event(event_type, content):
    try:
        with open("db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []

    data.append({
        "type": event_type,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })

    with open("db.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
