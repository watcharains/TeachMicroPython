# sender_joystick.py
import time, struct
from machine import ADC, Pin
import network, espnow

# -------------------------
# CONFIG — update as needed
# -------------------------
PIN_VRX = 4          # ADC pin for X
PIN_VRY = 5          # ADC pin for Y
PIN_BTN = 6          # Optional button (active-low); set to None to disable
SEND_HZ = 50          # Send rate
EMA_ALPHA = 0.25      # Smoothing (0..1), higher = less smoothing

# Put your receiver's MAC here (from receiver console)
PEER_MAC_STR = "7C:DF:A1:12:34:56"

# Calibration defaults (cover most joysticks). You can refine in runtime.
# Raw ADC is 0..4095 (12-bit) on ESP32 with ATTN_11DB
CAL = {
    "x_min": 300, "x_mid": 2000, "x_max": 3800,
    "y_min": 300, "y_mid": 2000, "y_max": 3800
}

# -------------------------
# Helpers
# -------------------------
def mac_from_str(s):
    return bytes(int(part, 16) for part in s.split(':'))

def init_wifi_espnow(peer_mac):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)             # STA mode must be active for ESP-NOW
    e = espnow.ESPNow()
    e.active(True)
    # Add peer (use channel=None to auto; you can specify channel if needed)
    try:
        e.add_peer(peer_mac)
    except OSError:
        # peer may already exist; ignore
        pass
    return sta, e

def setup_adc(pin_num):
    adc = ADC(Pin(pin_num))
    # Full 0-3.3V range
    adc.atten(ADC.ATTN_11DB)
    # 12-bit width is default on classic ESP32; set explicitly if your port supports it:
    try:
        adc.width(ADC.WIDTH_12BIT)
    except:
        pass
    return adc

def read_adc(adc):
    return adc.read()  # 0..4095 typically

def map_calibrated(v, vmin, vmid, vmax):
    # Map to 0..255 with center at ~128
    if v >= vmid:
        # mid..max -> 128..255
        top_span = max(1, vmax - vmid)
        return 128 + int(127 * (v - vmid) / top_span)
    else:
        # min..mid -> 0..127
        bot_span = max(1, vmid - vmin)
        return int(127 * (v - vmin) / bot_span)

def clamp8(n):
    return 0 if n < 0 else 255 if n > 255 else n

def read_button(pin):
    return 0 if pin.value() == 0 else 1  # 0 pressed, 1 not pressed (for clarity we send 0/1)

def quick_calibrate(adc_x, adc_y, seconds=2):
    """
    Quick auto-cal: ask user to move stick to extremes for ~2s.
    Updates CAL in place; skip if you like your fixed CAL.
    """
    print("Quick calibrating... move joystick to all extremes for", seconds, "seconds")
    t_end = time.ticks_add(time.ticks_ms(), int(seconds*1000))
    x_min = y_min = 4095
    x_max = y_max = 0
    x_sum = y_sum = 0
    n = 0
    while time.ticks_diff(t_end, time.ticks_ms()) > 0:
        vx = read_adc(adc_x)
        vy = read_adc(adc_y)
        x_min = min(x_min, vx); x_max = max(x_max, vx)
        y_min = min(y_min, vy); y_max = max(y_max, vy)
        x_sum += vx; y_sum += vy; n += 1
        time.sleep_ms(5)
    # Estimate mid as average during sweep (ok approximation)
    CAL["x_min"], CAL["x_max"], CAL["x_mid"] = x_min, x_max, x_sum // max(1, n)
    CAL["y_min"], CAL["y_max"], CAL["y_mid"] = y_min, y_max, y_sum // max(1, n)
    print("Cal done:", CAL)

def main():
    # Hardware
    adc_x = setup_adc(PIN_VRX)
    adc_y = setup_adc(PIN_VRY)
    btn_pin = None
    if PIN_BTN is not None:
        btn_pin = Pin(PIN_BTN, Pin.IN, Pin.PULL_UP)

    # Network
    peer_mac = mac_from_str(PEER_MAC_STR)
    sta, e = init_wifi_espnow(peer_mac)

    # Optional: run quick calibration once at boot
    # quick_calibrate(adc_x, adc_y, seconds=2)

    # Smoothing state (EMA)
    vx_ema = read_adc(adc_x)
    vy_ema = read_adc(adc_y)

    interval_ms = int(1000 / SEND_HZ)
    print("Sender started. Sending to", PEER_MAC_STR, "at", SEND_HZ, "Hz")

    while True:
        try:
            # Raw read
            vx = read_adc(adc_x)
            vy = read_adc(adc_y)

            # EMA smoothing
            vx_ema = int((1 - EMA_ALPHA) * vx_ema + EMA_ALPHA * vx)
            vy_ema = int((1 - EMA_ALPHA) * vy_ema + EMA_ALPHA * vy)

            # Map to 0..255 with calibration
            x8 = clamp8(map_calibrated(vx_ema, CAL["x_min"], CAL["x_mid"], CAL["x_max"]))
            y8 = clamp8(map_calibrated(vy_ema, CAL["y_min"], CAL["y_mid"], CAL["y_max"]))

            # Optional button
            btn = read_button(btn_pin) if btn_pin else 1  # 1 = not pressed (default)

            # Pack and send (3 bytes)
            payload = struct.pack('BBB', x8, y8, btn)
            e.send(peer_mac, payload)

            time.sleep_ms(interval_ms)
        except KeyboardInterrupt:
            break
        except Exception as ex:
            # If you see "ESPNowPeerError", peer may be missing/wrong; re-add peer.
            try:
                e.add_peer(peer_mac)
            except:
                pass
            # You can also print the error for debugging:
            # print("send err:", ex)
            time.sleep_ms(interval_ms)

if __name__ == "__main__":
    main()
