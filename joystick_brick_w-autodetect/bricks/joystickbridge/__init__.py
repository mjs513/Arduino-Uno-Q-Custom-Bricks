import requests

BASE_URL = "http://joystick:5000"



# ----------------------------------------------------
# Joystick initialization
# ----------------------------------------------------

def startJoystick():
    """Triggers the remote background device search and pairing engine loop."""
    url = f"{BASE_URL}/joystick/start"
    try:
        response = requests.post(url, timeout=45) # Long timeout to allow for the 10 setup sweeps
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Connection to bridge failed: {e}"}

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

