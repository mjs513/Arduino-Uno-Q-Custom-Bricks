# app.py
from joystick_helper import Joystick
import threading
from flask import Flask, jsonify

app = Flask(__name__)

# Use the EVDEV device mapped inside Docker
js = Joystick()
threading.Thread(target=js.loop, daemon=True).start()

# ----------------------------------------------------
# Joystick metadata
# ----------------------------------------------------
@app.route("/joystick/state")
def js_state():
    return jsonify(js.get_state())

@app.route("/joystick/name")
def js_name():
    return jsonify({"name": js.name})

@app.route("/joystick/num_axes")
def js_num_axes():
    return jsonify({"num_axes": js.get_num_axes()})

@app.route("/joystick/num_buttons")
def js_num_buttons():
    return jsonify({"num_buttons": js.get_num_buttons()})

@app.route("/joystick/axis_map")
def js_axis_map():
    return jsonify({"axis_map": js.get_axis_map()})

@app.route("/joystick/button_map")
def js_button_map():
    return jsonify({"button_map": js.get_button_map()})

# ----------------------------------------------------
# Joystick live state
# ----------------------------------------------------
@app.route("/joystick/axes")
def js_axes():
    return jsonify(js.get_axis_values())

@app.route("/joystick/buttons")
def js_buttons():
    return jsonify(js.get_button_values())
