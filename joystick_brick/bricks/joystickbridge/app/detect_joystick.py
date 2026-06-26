import os
from evdev import InputDevice

def find_gamepad_event():
    base = "/dev/input"

    # Known naming patterns for PS4 and Xbox controllers
    ps4_names = [
        "sony",
        "wireless controller",
        "dualshock",
        "playstation"
    ]

    xbox_names = [
        "xbox",
        "microsoft",
        "xbox wireless controller",
        "xbox one",
        "xbox360",
        "xbox 360"
    ]

    for name in os.listdir(base):
        if not name.startswith("event"):
            continue

        path = os.path.join(base, name)

        try:
            dev = InputDevice(path)
            dev_name = dev.name.lower()

            # Match PS4
            if any(tag in dev_name for tag in ps4_names):
                return path

            # Match Xbox
            if any(tag in dev_name for tag in xbox_names):
                return path

        except Exception:
            continue

    return None
