# joystick_evdev.py
import threading
from evdev import InputDevice, ecodes
from detect_joystick import find_gamepad_event

class Joystick:
    def __init__(self, device=None):
        if device is None:
            device = find_gamepad_event()

        if device is None:
            raise RuntimeError("No PS4 controller detected")

        self.device_path = device
        self.dev = None

        self.axis_map = []
        self.button_map = []
        self.axis_states = {}
        self.button_states = {}

        self.num_axes = 0
        self.num_buttons = 0
        self.name = ""

        self.running = False
        self.lock = threading.Lock()

    # ----------------------------------------------------
    # Initialization
    # ----------------------------------------------------
    def open(self):
        self.dev = InputDevice(self.device_path)
        self.name = self.dev.name

        caps = self.dev.capabilities(verbose=False)

        # Accept ALL axes the device reports
        abs_caps = caps.get(ecodes.EV_ABS, [])
        self.axis_map = [code for code, _info in abs_caps]
        self.num_axes = len(self.axis_map)

        # Accept ALL buttons the device reports
        key_caps = caps.get(ecodes.EV_KEY, [])
        self.button_map = list(key_caps)
        self.num_buttons = len(self.button_map)

        # Initialize states
        with self.lock:
            for a in self.axis_map:
                self.axis_states[a] = 0
            for b in self.button_map:
                self.button_states[b] = 0

    # ----------------------------------------------------
    # Background event loop
    # ----------------------------------------------------
    def loop(self):
        self.running = True
        self.open()

        for event in self.dev.read_loop():
            if not self.running:
                break

            with self.lock:
                # Accept ALL axis events
                if event.type == ecodes.EV_ABS:
                    self.axis_states[event.code] = event.value

                # Accept ALL button events
                elif event.type == ecodes.EV_KEY:
                    self.button_states[event.code] = event.value

    # ----------------------------------------------------
    # Public API (drop‑in compatible)
    # ----------------------------------------------------
    def get_num_axes(self):
        return self.num_axes

    def get_num_buttons(self):
        return self.num_buttons

    def get_axis_map(self):
        return list(self.axis_map)

    def get_button_map(self):
        return list(self.button_map)

    def get_axis_values(self):
        with self.lock:
            return dict(self.axis_states)

    def get_button_values(self):
        with self.lock:
            return dict(self.button_states)

    def get_state(self):
        with self.lock:
            return {
                "axes": dict(self.axis_states),
                "buttons": dict(self.button_states),
            }
