# main.py
import time
import joystickbridge as joystick

# ----------------------------------------------------
# PS4 Axis + Button Names (EVDEV codes)
# ----------------------------------------------------
AXIS_NAMES = {
    0: "lx",      # ABS_X
    1: "ly",      # ABS_Y
    2: "rx",      # ABS_RX
    5: "ry",      # ABS_RY

    3: "L2 Analog", 
    4: "R2 Analog", 
    9: "R2 Analog", 
    10: "L2 Analog", 

    16: "dpad_x", # ABS_HAT0X
    17: "dpad_y", # ABS_HAT0Y
}

AXIS_ORDER = [
    0,   # lx
    1,   # ly
    2,   # rx
    5,   # ry
    3,   # l2 analog
    4,   # r2 analog
    10,
    9,
    16,  # dpad_x
    17,  # dpad_y
]

BUTTON_NAMES = {
    305: "cross",      # BTN_SOUTH
    306: "circle",     # BTN_EAST
    307: "triangle",   # BTN_NORTH
    304: "square",     # BTN_WEST

    308: "l1/Y",         # BTN_TL
    309: "r1",         # BTN_TR
    310: "l2_btn",     # BTN_TL2
    311: "r2_btn",     # BTN_TR2

    312: "share",      # BTN_SELECT
    313: "options",    # BTN_START
    316: "ps",         # BTN_MODE

    314: "l3",         # BTN_THUMBL
    315: "r3/options",         # BTN_THUMBR

    317: "touchpad/Stl Lt Bth",   # Touchpad click

    318: "Stick Rt Btn",

    # Firmware-dependent:
    158: "share",   # sometimes "back" on older firmware
    172: "guide",   # sometimes "xbox" on older firmware
}

BUTTON_ORDER = [
    158,
    172,
    305,  # cross
    306,  # circle
    307,  # triangle
    304,  # square

    308,  # L1
    309,  # R1
    310,  # L2 click
    311,  # R2 click

    312,  # share
    313,  # options
    316,  # ps

    314,  # L3
    315,  # R3

    317,  # touchpad
    318,
]

# ----------------------------------------------------
# Inspector Class (Pretty Printing)
# ----------------------------------------------------
class Inspector:
    def __init__(self):
        self.last_axes = {}
        self.last_buttons = {}

    def button_label(self, code):
        return BUTTON_NAMES.get(code, f"btn_{code}")

    def print_changes(self, axes, buttons):
        changed = False

        # AXES
        for raw_code, value in axes.items():
            #print("DEBUG:", axes)
            code = int(raw_code)
            name = AXIS_NAMES.get(code, f"axis_{code}")

            old = self.last_axes.get(code)
            if old is None or old != value:
                delta = 0 if old is None else value - old
                print(f"Axis {name:<8} {value:>7.3f} (Δ {delta:+7.3f})")
                self.last_axes[code] = value
                changed = True

        # BUTTONS
        for raw_code, value in buttons.items():
            #print("DEBUG:", buttons)
            code = int(raw_code)
        
            old = self.last_buttons.get(code)
            if old is None or value != old:
                name = self.button_label(code)
                print(f"Button {name:<10} {value}")
                self.last_buttons[code] = value
                changed = True

        return changed


# ----------------------------------------------------
# MAIN
# ----------------------------------------------------
def main():
    print("=== PS4 EVDEV Joystick Test ===")
    
    # Metadata
    try:
        name = joystick.getName()
        print("Joystick Name:", name)

        num_axes = joystick.getNumAxes()
        print("Number of Axes:", num_axes)

        num_buttons = joystick.getNumButtons()
        print("Number of Buttons:", num_buttons)

        axis_map = joystick.getAxisMap()
        print("RAW axis_map:", axis_map)

        button_map = joystick.getButtonMap()
        print("RAW button_map:", button_map)

    except Exception as e:
        print("Error reading joystick metadata:", e)
        return

    print("\n=== Live Joystick State ===")

    inspector = Inspector()

    while True:
        try:
            state = joystick.getState()
    
            # Convert keys to integers
            axes = {int(k): v for k, v in state.get("axes", {}).items()}
            buttons = {int(k): v for k, v in state.get("buttons", {}).items()}
    
            # Build fixed arrays
            axis_values = [axes.get(code, 0) for code in AXIS_ORDER]
            button_values = [buttons.get(code, 0) for code in BUTTON_ORDER]
    
            if inspector.print_changes(axes, buttons):
                print("AX:", axis_values)
                print("BT:", button_values)
                print()
    
        except Exception as e:
            print("Error reading joystick state:", e)
    
        time.sleep(0.01)



if __name__ == "__main__":
    main()
