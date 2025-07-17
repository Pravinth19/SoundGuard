import network
import socket
import ujson
import _thread
import time
from machine import Pin, PWM
from nextion import display_value, set_wifi_icon, show_alarm, display_status
from web_config import start_webserver, load_config

# Konfiguration laden
config = load_config()

# Aktuelle Messdaten
latest_data = {
    "node1": {"device_id": "node1", "db_level": 0.0},
    "node2": {"device_id": "node2", "db_level": 0.0}
}

# Buzzer Setup
buzzer = PWM(Pin(25), freq=3000, duty=0)

def set_buzzer(active):
    if active:
        buzzer.freq(3000)
        buzzer.duty(512)
    else:
        buzzer.duty(0)

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
    display_value("node1", latest_data["node1"]["db_level"])
    display_value("node2", latest_data["node2"]["db_level"])

def save_log_entry(device_id, db_level):
    try:
        timestamp = time.localtime()
        timestr = "{:02d}:{:02d}:{:02d}".format(timestamp[3], timestamp[4], timestamp[5])
        with open("log.txt", "a") as f:
            f.write(f"{timestr},{device_id},{db_level:.1f} dB\n")
    except Exception as e:
        print("Fehler beim Log-Speichern:", e)

def udp_loop(udp):
    global last_update_time
    while True:
        try:
            data, _ = udp.recvfrom(1024)
            json_data = ujson.loads(data)
            device_id = json_data.get("device_id")
            db_level = float(json_data.get("db_level", 0))

            if device_id in latest_data:
                latest_data[device_id]["db_level"] = db_level
                update_display()
                save_log_entry(device_id, db_level)

                if db_level > config["threshold"]:
                    print(f"Laerm ueber Schwelle bei {device_id}: {db_level} dB")
                    show_alarm(True)
                    display_status(f"ALARM: {device_id}")
                    set_buzzer(True)
                else:
                    show_alarm(False)
                    display_status("OK")
                    set_buzzer(False)

            last_update_time = time.ticks_ms()
            set_wifi_icon(True)

        except Exception as e:
            print("Fehler beim Empfang:", e)

def monitor_connection():
    global last_update_time
    while True:
        if time.ticks_diff(time.ticks_ms(), last_update_time) > 10000:
            print("Keine Verbindung zu Sensoren")
            set_wifi_icon(False)
            display_status("Keine Verbindung")
            show_alarm(False)
            set_buzzer(False)
        time.sleep(5)

# Start
last_update_time = time.ticks_ms()
ap = start_ap()
udp = setup_udp()

_thread.start_new_thread(start_webserver, (lambda: latest_data,))
_thread.start_new_thread(monitor_connection, ())

udp_loop(udp)
