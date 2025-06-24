import network
import socket
import ujson
import _thread
from nextion import display_value
from web_config import start_webserver, load_config

config = load_config()

latest_data = {
    "node1": {"device_id": "node1", "db_level": 0},
    "node2": {"device_id": "node2", "db_level": 0}
}

def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="Master", password="password", authmode=3)
    while not ap.active():
        pass
    print("Access Point aktiv:", ap.ifconfig())
    return ap

def setup_udp(port=4210):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', port))
    return s

def update_display():
    display_value("N1", latest_data["node1"]["db_level"])
    display_value("N2", latest_data["node2"]["db_level"])

def udp_loop(udp):
    while True:
        try:
            data, _ = udp.recvfrom(1024)
            json_data = ujson.loads(data)
            device_id = json_data.get("device_id")
            if device_id in latest_data:
                latest_data[device_id] = json_data
                update_display()
                if json_data["db_level"] > config["threshold"]:
                    print(f"Lärm über Grenzwert bei {device_id}!")
        except Exception as e:
            print("Fehler beim Empfang:", e)

ap = start_ap()
udp = setup_udp()
_thread.start_new_thread(start_webserver, (lambda: latest_data,))
udp_loop(udp)
