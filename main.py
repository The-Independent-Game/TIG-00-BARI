import time
import network
import tig_00_bari
import wifi_config

def connect_wifi():
    print("Connessione WiFi in corso...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print(f"WiFi already connected IP: {wlan.ifconfig()[0]}")
        return True

    print(f"Connecting to {wifi_config.WIFI_SSID}...")
    wlan.connect(wifi_config.WIFI_SSID, wifi_config.WIFI_PASSWORD)

    timeout = wifi_config.WIFI_TIMEOUT
    while timeout > 0:
        if wlan.isconnected():
            print(f"WiFi connected IP: {wlan.ifconfig()[0]}")
            return True
        time.sleep(1)
        timeout -= 1
        print(f"waiting ... ({timeout}s)")

    print("Timeout connection ")
    return False

def main():
    connected = connect_wifi()
    tig_00_bari.start(connected)

if __name__ == "__main__":
    main()
