
import network, espnow, time, struct

def init_wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    # No connection needed for ESP-NOW, just ensure STA is on.
    return sta

def init_espnow():
    e = espnow.ESPNow()
    e.active(True)
    return e

def mac_str(mac_bytes):
    return ':'.join('{:02X}'.format(b) for b in mac_bytes)

def main():
    sta = init_wifi()
    e = init_espnow()
    print("Receiver ready. My MAC:", mac_str(sta.config('mac')))
    print("Waiting for joystick packets...")

    while True:
        try:
            host, msg = e.recv()  # non-blocking by default; returns (None, None) if nothing
            if host and msg:
                # Expect 3 bytes: x(0-255), y(0-255), btn(0/1)
                if len(msg) == 3:
                    x, y, btn = struct.unpack('BBB', msg)
                    print("From", mac_str(host), "X:", x, "Y:", y, "BTN:", btn)
                else:
                    print("From", mac_str(host), "raw:", msg)
        except KeyboardInterrupt:
            break
        except Exception as ex:
            print("recv err:", ex)
        time.sleep_ms(5)

if __name__ == "__main__":
    main()
