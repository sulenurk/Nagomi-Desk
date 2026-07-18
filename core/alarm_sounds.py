from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


ALARM_SOUNDS = {
    "analog": {
        "name_key": "alarm_analog",
        "file": "assets/sounds/analog.mp3"
    },
    "beep": {
        "name_key": "alarm_beep",
        "file": "assets/sounds/beep.mp3"
    },
    "birdy": {
        "name_key": "alarm_birdy",
        "file": "assets/sounds/birdy.mp3"
    },
    "buzz": {
        "name_key": "alarm_buzz",
        "file": "assets/sounds/buzz.mp3"
    },
    "dans": {
        "name_key": "alarm_dans",
        "file": "assets/sounds/dans.mp3"
    },
    "galaxy": {
        "name_key": "alarm_galaxy",
        "file": "assets/sounds/galaxy.mp3"
    },
}


def get_alarm_path(alarm_id):
    alarm_data = ALARM_SOUNDS.get(alarm_id)

    if not alarm_data:
        return None

    relative_path = alarm_data.get("file")

    if not relative_path:
        return None

    return PROJECT_ROOT / relative_path