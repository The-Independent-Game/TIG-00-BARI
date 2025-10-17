import time
import network
import tig_00_bari
import wifi_config


def connect_wifi():
    """
    Connette il Pico W al WiFi usando le credenziali da wifi_config.py
    Ritorna True se connesso, False altrimenti
    """
    print("Connessione WiFi in corso...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("WiFi già connesso")
        print(f"IP: {wlan.ifconfig()[0]}")
        return True

    print(f"Connessione a {wifi_config.WIFI_SSID}...")
    wlan.connect(wifi_config.WIFI_SSID, wifi_config.WIFI_PASSWORD)

    # Attendi connessione con timeout
    timeout = wifi_config.WIFI_TIMEOUT
    while timeout > 0:
        if wlan.isconnected():
            print("WiFi connesso!")
            print(f"IP: {wlan.ifconfig()[0]}")
            return True
        time.sleep(1)
        timeout -= 1
        print(f"Attendo connessione... ({timeout}s)")

    print("Timeout connessione WiFi")
    return False

def main():
    connect_wifi()
    tig_00_bari.start()

if __name__ == "__main__":
    main()
