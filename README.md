# Arduino-Uno-Q-Custom-Bricks

This repo contains 2 custom bricks and an example app to use both bricks in the same app

**spibridge** - A custom brick to use SPI3 to transfer data between MCU and MPU and vice-versa
**joystick_brick** - A custom brick to use get data from a PS4 Dual Shock or XBox Controller
**spi-joystick-bridge** - A custom app using both bricks in one app to transfer joystick data from the MPU to the MCU.


# NOTES ON DEVELOPING CUSTOM Bricks

# Notes on putting brick images on Docker Hub  

## 1. Create a docker hub account: Docker Hub Container Image Library | App Containerization
## 2. Build your custom brick.
## 3. find your brick image file by doing `docker images`. For the joystick it was
```
joystick_brick-joystick
```
## 4. Tag the image file:
```
docker tag joystick_brick-joystick mjs513/joystick_brick-joystick
```
or if you want to use versioning:
```
docker tag joystick_brick-joystick mjs513/joystick_brick-joystick:latest
docker tag joystick_brick-joystick mjs513/joystick_brick-joystick:1.0.0
```
## 5. Push the image to docker hub
```
docker push mjs513/joystick_brick-joystick
or
docker push mjs513/joystick_brick-joystick:latest
or
docker push mjs513/joystick_brick-joystick:1.0.0

depending on what tag you used
```
Now you can keep reusing that image between apps 
## 6. Comments
This has a couple of advantages

- It is using a prebuilt image
- If its already installed it wont reinstall another copy may update if you change it.
- Easier to use when you want to use it on the Q2 (2gb version)  

# Reusing a Custom Brick

## 1. Create a new app
## 2.  Create a new Custom Brick and call it `joystickbridge`
## 3.  After creating the brick you will see the following structure
```yaml
├── app.yaml
├── bricks
│   └── joystick
│       ├── brick_compose.yaml
│       ├── brick_config.yaml
│       ├── __init__.py
│       └── README.md
├── python
│   └── main.py
├── README.md
└── sketch
    ├── sketch.ino
    └── sketch.yaml
```
## 4.  Now for the fun part.
### a.  Copy the original brick_compose.yaml from the joystick brick
```yaml
# Source: https://forum.arduino.cc/t/getting-a-neato-xv-11-lidar-working-on-the-q/1445568/18
services:
  joystick:
    # App Lab will automatically look for the Dockerfile in the same folder
    build:
      context: .

    develop:
      # Configure `docker compose watch` to automatically rebuild the container when image source files are modified.
      # See: https://docs.docker.com/compose/how-tos/file-watch/
      watch:
        - action: rebuild
          path: ./app
        - action: rebuild
          path: brick_compose.yaml
        - action: rebuild
          path: Dockerfile
        - action: restart
          path: __init__.py

    privileged: true

    group_add:
      - "995"

    devices:
      - "/dev/input:/dev/input"

    ports:
      # Expose the port for communication with the container's Flask web application.
      # See: https://docs.docker.com/reference/compose-file/services/#ports
      - "5000:5000"
```
and edit it so it looks like
```yaml
# Source: https://forum.arduino.cc/t/getting-a-neato-xv-11-lidar-working-on-the-q/1445568/18
services:
  joystick:
    # image is pulled from docker hub
    image: mjs513/joystick_brick-joystick

    privileged: true

    group_add:
      - "995"

    devices:
      - "/dev/input:/dev/input"

    ports:
      # Expose the port for communication with the container's Flask web application.
      # See: https://docs.docker.com/reference/compose-file/services/#ports
      - "5000:5000"
```

**Note that I changed the build joystick bridge to pull an prebuilt image from docker hub that I already created and pushed to docker hub.  More on how to do that later.**

### b.  Copy the joystick bridge `__init__.py` from your original joystick bridge app or from my app which should look like
```python
import requests

BASE_URL = "http://joystick:5000"

# ----------------------------------------------------
# Joystick metadata
# ----------------------------------------------------
def getName():
    url = f"{BASE_URL}/joystick/name"
    return requests.get(url).json()

def getNumAxes():
    url = f"{BASE_URL}/joystick/num_axes"
    return requests.get(url).json()

def getNumButtons():
    url = f"{BASE_URL}/joystick/num_buttons"
    return requests.get(url).json()

def getAxisMap():
    url = f"{BASE_URL}/joystick/axis_map"
    return requests.get(url).json()

def getButtonMap():
    url = f"{BASE_URL}/joystick/button_map"
    return requests.get(url).json()

# ----------------------------------------------------
# Joystick live state
# ----------------------------------------------------
def getAxes():
    url = f"{BASE_URL}/joystick/axes"
    return requests.get(url).json()

def getButtons():
    url = f"{BASE_URL}/joystick/buttons"
    return requests.get(url).json()

def getState():
    url = f"{BASE_URL}/joystick/state"
    return requests.get(url).json()

```

### c. no changes needed to `brick_config.yaml`

## 5.  Edit python `main.py` to use the bridge`.  For example:
```python
# main.py
import time
# Note `import <brick name> as joystick
import joystick as joystick

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
```

## 6. Then RUN it and you should see
```
======== App is starting ============================
=== PS4 EVDEV Joystick Test ===
Joystick Name: {'name': 'Sony Computer Entertainment Wireless Controller'}
Number of Axes: {'num_axes': 8}
Number of Buttons: {'num_buttons': 14}
RAW axis_map: {'axis_map': [0, 1, 2, 3, 4, 5, 16, 17]}
RAW button_map: {'button_map': [304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317]}
=== Live Joystick State ===
Axis lx         0.000 (Δ  +0.000)
Axis ly         0.000 (Δ  +0.000)
Axis rx         0.000 (Δ  +0.000)
Axis L2 Analog   0.000 (Δ  +0.000)
Axis R2 Analog   0.000 (Δ  +0.000)
Axis ry         0.000 (Δ  +0.000)
Axis dpad_x     0.000 (Δ  +0.000)
Axis dpad_y     0.000 (Δ  +0.000)
Button square     0
Button cross      0
Button circle     0
Button triangle   0
Button l1/Y       0
Button r1         0
Button l2_btn     0
Button r2_btn     0
Button share      0
Button options    0
Button l3         0
Button r3/options 0
Button ps         0
Button touchpad/Stl Lt Bth 0
AX: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
BT: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Axis lx        69.000 (Δ +69.000)
AX: [69, 0, 0, 0, 0, 0, 0, 0, 0, 0]
BT: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Axis lx         0.000 (Δ -69.000)
AX: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
BT: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Axis lx        21.000 (Δ +21.000)
AX: [21, 0, 0, 0, 0, 0, 0, 0, 0, 0]
BT: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Axis lx       112.000 (Δ +91.000)
AX: [112, 0, 0, 0, 0, 0, 0, 0, 0, 0]
BT: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Axis lx       128.000 (Δ +16.000)
AX: [128, 0, 0, 0, 0, 0, 0, 0, 0, 0]
BT: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
```

**One note: Data will only print when data changes.**

# Using 2 Bricks in the Same App

Duplicate the SPI3Bridge demo app (easier than copying stuff to start and rename it to say SPI Joystick Bridge.
delete app and samples directory and the Dockerfile
Follow steps in previous post to create a joystickbridge Custom Brick.

1. Modify the brick_compose.yaml to this
```yaml
# Source: https://forum.arduino.cc/t/getting-a-neato-xv-11-lidar-working-on-the-q/1445568/18
# Source: Anyone had luck reading from a gamepad? - UNO Family / UNO Q - Arduino Forum
services:

  spi3bridge:
    # Use the prebuilt Docker Hub image for the SPI bridge.
    # This container runs a Flask server that exposes SPI read/write endpoints.
    image: mjs513/spibridge-spi3bridge

    # Pass the physical SPI device from the host into the container.
    # This allows Python inside the container to talk directly to the UNO Q SPI bus.
    devices:
      - "/dev/spidev0.0:/dev/spidev0.0"

    ports:
      # Map container port 5000 → host port 5000.
      # Your client code will call http://localhost:5000 to talk to the SPI bridge.
      - "5000:5000"


  joystickbridge:
    # Use the prebuilt Docker Hub image for the joystick bridge.
    # This container runs a Flask server that exposes joystick state via HTTP.
    image: mjs513/joystick_brick-joystick

    # Required because joystick devices under /dev/input often need elevated permissions.
    privileged: true

    # Add the host group with GID 995 into the container.
    # This is usually the group that owns /dev/input/event* on the host.
    # Without this, the container may not have permission to read joystick events.
    group_add:
      - "995"

    devices:
      # Pass the entire /dev/input directory into the container.
      # This includes js0, event-joystick, and other input devices.
      # The container can then open /dev/input/event-joystick directly.
      - "/dev/input:/dev/input"

    ports:
      # Map container port 5000 → host port 5001.
      # Your client code will call http://localhost:5001 to talk to the joystick bridge.
      - "5001:5000"
```
Note that the compose file now references the two bricks. So what does all that junk actually mean:

### 1. image:

You’re using prebuilt images, not building locally. This is ideal for bricks because the images are stable and versioned.

### 2. devices:

This is the critical part for hardware access.

/dev/spidev0.0 → gives the SPI bridge direct access to the UNO Q SPI bus
/dev/input → gives the joystick bridge access to Linux input events
Without these, the containers would run, but the hardware APIs would fail.

### 3. privileged: true (joystick only)

Joystick devices often require:
- raw input event access
- udev rules
- elevated permissions
- privileged: true ensures the container can read /dev/input/eventwithout permission errors.

###4. group_add: 995

On many Linux systems, `/dev/input/event* ` belongs to a group like:

```
crw-rw---- 1 root input 13, 64 ...
```
If the group ID is 995, adding it ensures:

- the container user belongs to the same group
- the container can read joystick events without running as root

### 5. ports:

You expose two separate HTTP APIs:

| Service        | Container Port | Host Port | Purpose            |
| :------------- | :------------- | :-------- | :----------------- |
| spi3bridge     | 5000           | 5000      | SPI read/write API |
| joystickbridge | 5000           | 5001      | Joystick state API |

This prevents port conflicts and keeps the APIs cleanly separated.

Modify the joystickbridge brick __init__.py to change the existing base url to

```python
# Allow the code to work both inside Docker (host = "joystickbridge") and on the host machine (override via JOYSTICK_HOST).
# BASE_URL is built dynamically so the same script runs in any environment without hard‑coding localhost.
JOYSTICK_HOST = os.getenv("JOYSTICK_HOST", "joystickbridge")
BASE_URL = f"http://{JOYSTICK_HOST}:5000"
```

This avoid conflicts between ports.

When all finished your new app should have the following structure:
```
├── app.yaml
├── bricks
│   ├── joystickbridge
│   │   ├── __init__.py
│   │   └── __pycache__
│   └── spibridge
│       ├── brick_compose.yaml
│       ├── brick_config.yaml
│       ├── __init__.py
│       ├── __pycache__
│       └── README.md
├── python
│   ├── main.py
│   └── requirements.txt
├── README.md
└── sketch
    ├── sketch.ino
    ├── sketch.yaml
    └── SPIPeripheral.h
 ```


## NOTE.  
Posted three images on docker hub for resuse
mjs513/joystickbridge_autodetect
mjs513/joystick_brick-joystick
mjs513/spibridge-spi3bridge
