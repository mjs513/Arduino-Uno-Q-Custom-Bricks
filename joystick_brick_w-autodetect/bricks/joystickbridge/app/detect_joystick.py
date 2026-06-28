import os
import re
import time
import subprocess
import logging
import pexpect
from evdev import InputDevice

logger = logging.getLogger("Joystick_Detection")

# -------------------------------------------------------------------------
# Embedded Bluetoothctl Engine
# 
# based on https://github.com/lecchereng/BluetoothCTL and modified by
# Google Gemini
# -------------------------------------------------------------------------
class BluetoothctlEngine:
    """A minimal, self-contained client to manage containerized Bluetooth connections."""
    def __init__(self):
            # Setup the expected prompts modern bluetoothctl builds use
            self.__expected_common = ["Invalid argument", "Invalid command", "#", "bluetoothctl", ">", pexpect.EOF]
            
            # 1. Attempt to clear any low-level kernel blocks
            try:
                subprocess.check_output("rfkill unblock bluetooth", shell=True, stderr=subprocess.DEVNULL)
            except Exception:
                pass
                
            # 2. Spawn the bluetoothctl interactive process
            self.__process = pexpect.spawnu("bluetoothctl", echo=False)
            
            try:
                self.__process.expect(["Agent registered"] + self.__expected_common, timeout=3)
            except pexpect.exceptions.TIMEOUT:
                pass
    
            # 3. EXPLICITLY POWER ON AND REGISTER THE AGENT
            logger.info("Initializing container Bluetooth radio power state...")
            
            # Send power on command
            self.__process.send("power on\n")
            time.sleep(1.5)
    
            # Send agent on command (ensures pairing passkeys/handshakes are accepted automatically)
            self.__process.send("agent on\n")
            time.sleep(1)
            
            # Set the controller to default just in case multiple adapters exist
            self.__process.send("default-agent\n")
            time.sleep(1)
            
            # Flush the initialization output buffer so it doesn't pollute our scanner
            try:
                self.__process.expect(self.__expected_common, timeout=1)
            except pexpect.exceptions.TIMEOUT:
                pass

    def clean_output(self, output: str) -> str:
        output = re.compile("\\x1b\\[\\?[0-9a-zA-Z;]+\\x1b\\[[0-9a-zA-Z;]+[^\\]]+\\]\\x1b\\[[0-9a-zA-Z;]+").sub("", output)
        output = re.compile("\\[?\\x1b\\[\\??[\\?0-9a-zA-Z;\r\n]+\\]?").sub("", output)
        return output.strip().replace("\r", "")

    def get_paired_controllers(self) -> list:
            """Looks in Bluetooth memory for already paired or cached controllers."""
            # 'devices' shows all paired and known controller nodes in system memory
            self.__process.send("devices\n")
            time.sleep(1.5)
            try:
                self.__process.expect(self.__expected_common, timeout=2)
                buffer = self.clean_output(self.__process.before)
            except pexpect.exceptions.TIMEOUT:
                buffer = self.clean_output(self.__process.buffer)
                
            # Highly aggressive regex to capture any common controller MAC address pattern
            pattern = r"Device\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})\s+.*(Wireless|Xbox|Sony|DualShock|Controller)"
            found_macs = [match.group(1) for match in re.finditer(pattern, buffer, re.IGNORECASE)]
            
            # Remove duplicates while preserving order
            return list(dict.fromkeys(found_macs))

    def scan_and_discover_mac(self, scan_duration: int = 10) -> str:
            """Actively listens for PS4 or Xbox controllers in pairing mode."""
            self.__process.send("scan on\n")
            
            target_patterns = [
                r"Device\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})\s+.*Controller",
                r"Device\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})\s+.*Wireless",
                r"([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})" # absolute fallback regex
            ]
            
            start_time = time.time()
            discovered_mac = None
            
            while time.time() - start_time < scan_duration:
                try:
                    self.__process.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=1)
                    buffer = self.clean_output(self.__process.before)
                    
                    # Filter out obvious non-controller keywords if the absolute fallback triggers
                    ignore_keywords = ["phone", "tv", "audio", "headset", "macbook", "laptop"]
                    
                    for pattern in target_patterns:
                        match = re.search(pattern, buffer, re.IGNORECASE)
                        if match:
                            potential_mac = match.group(1)
                            if not any(bad in buffer.lower() for bad in ignore_keywords):
                                discovered_mac = potential_mac
                                break
                except Exception:
                    pass
                if discovered_mac:
                    break
                    
            self.__process.send("scan off\n")
            time.sleep(1)
            return discovered_mac

    def scan_and_discover_mac(self, scan_duration: int = 10) -> str:
        """Actively listens for PS4 or Xbox controllers in pairing mode."""
        self.__process.send("scan on\n")
        
        target_patterns = [
            r"Device\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})\s+Wireless\s+Controller",
            r"Device\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})\s+Xbox\s+Wireless\s+Controller"
        ]
        
        start_time = time.time()
        discovered_mac = None
        
        while time.time() - start_time < scan_duration:
            try:
                # Short timeout to continually cycle and inspect incoming lines
                self.__process.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=1)
                buffer = self.clean_output(self.__process.before)
                
                for pattern in target_patterns:
                    match = re.search(pattern, buffer, re.IGNORECASE)
                    if match:
                        discovered_mac = match.group(1)
                        break
            except Exception:
                pass
            if discovered_mac:
                break
                
        self.__process.send("scan off\n")
        time.sleep(1)
        return discovered_mac

    def run_handshake(self, mac_addr: str):
        """Pairs, trusts, and links the targeted controller."""
        # Pair
        self.__process.send(f"pair {mac_addr}\n")
        time.sleep(4)
        # Trust
        self.__process.send(f"trust {mac_addr}\n")
        time.sleep(2)
        # Connect
        self.__process.send(f"connect {mac_addr}\n")
        time.sleep(4)

    def run_disconnect(self, mac_addr: str):
        self.__process.send(f"disconnect {mac_addr}\n")
        time.sleep(1.5)

# -------------------------------------------------------------------------
# Core Device Lookup Logic
# -------------------------------------------------------------------------
def scan_evdev_for_gamepad():
    """Scans /dev/input for known hardware naming patterns."""
    base = "/dev/input"
    if not os.path.exists(base):
        return None

    ps4_names = ["sony", "wireless controller", "dualshock", "playstation"]
    xbox_names = ["xbox", "microsoft", "xbox wireless controller", "xbox one", "xbox360", "xbox 360"]

    for name in os.listdir(base):
        if not name.startswith("event"):
            continue

        path = os.path.join(base, name)
        try:
            dev = InputDevice(path)
            dev_name = dev.name.lower()

            if any(tag in dev_name for tag in ps4_names) or any(tag in dev_name for tag in xbox_names):
                return path
        except Exception:
            continue
    return None

def find_gamepad_event():
    """
    Main detection function entry point for the Arduino Uno Q brick.
    Attempts to find or connect a controller with up to 10 retries.
    """
    MAX_RETRIES = 50
    RETRY_DELAY_SECONDS = 3

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"--- Gamepad Detection Attempt {attempt}/{MAX_RETRIES} ---")

        # Step 1: Check if the controller is already connected physically or wirelessly
        device_path = scan_evdev_for_gamepad()
        if device_path:
            logger.info(f"✨ Success! Gamepad detected at: {device_path}")
            return device_path

        # Step 2: Fallback to Bluetooth Automation because no input device was found
        logger.warning("No active gamepad event stream found. Initializing Bluetooth fallback engine...")
        try:
            bt = BluetoothctlEngine()
            
            # A. Check if the controller was paired previously and is just turned off
            paired_macs = bt.get_paired_controllers()
            if paired_macs:
                logger.info(f"Found {len(paired_macs)} previously paired controller(s). Attempting wake-up connection...")
                for mac in paired_macs:
                    bt.run_handshake(mac)
            else:
                # B. If nothing is paired, look for a new controller flashing in sync mode
                logger.info("No paired devices in memory. Scanning for controllers in pairing mode...")
                discovered_mac = bt.scan_and_discover_mac(scan_duration=10)
                if discovered_mac:
                    logger.info(f"Discovered new controller: {discovered_mac}. Pairing...")
                    bt.run_handshake(discovered_mac)
                else:
                    logger.warning("Bluetooth pairing window closed. No controller discovered on this sweep.")

            # Give the Linux kernel input subsystem a moment to mount the /dev/input node
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Bluetooth engine encountered an error during this sweep: {e}")

        # Final sweep check for this specific iteration loop pass
        device_path = scan_evdev_for_gamepad()
        if device_path:
            logger.info(f"✨ Success! Gamepad mounted after Bluetooth setup phase at: {device_path}")
            return device_path

        # If we reach here, this attempt failed. Wait before trying again.
        if attempt < MAX_RETRIES:
            logger.warning(f"Attempt {attempt} failed to acquire controller. Retrying in {RETRY_DELAY_SECONDS} seconds...")
            time.sleep(RETRY_DELAY_SECONDS)

    # If the loop finishes without returning a valid path
    logger.critical("❌ All 10 discovery and pairing attempts exhausted. No gamepad could be initialized.")
    return None

def disconnect_active_gamepads():
    logger.info("Application shutdown initiated. Forcing low-level Bluetooth disconnect...")
    try:
        # Query connected input devices via bluez system tools and force disconnect them instantly
        # This bypasses the interactive bluetoothctl process entirely for maximum shutdown speed
        subprocess.run("bluetoothctl disconnect", shell=True, timeout=2)
        logger.info("Bluetooth cleanup complete.")
    except Exception as e:
        logger.error(f"Quick disconnect failed: {e}")