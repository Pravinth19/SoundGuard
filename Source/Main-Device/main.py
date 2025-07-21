import network
import socket
import ujson
import _thread
import time
from machine import Pin, PWM
from nextion import display_value, set_wifi_icon, show_alarm, send_cmd, uart
from web_config import start_webserver, load_config, save_config

# Konfiguration laden
config = load_config()
threshold = config.get("threshold", 85)

# Aktuelle Messdaten
latest_data = {
    "node1": {"device_id": "node1", "db_level": 0.0},
    "node2": {"device_id": "node2", "db_level": 0.0}
}

# Buzzer Setup
buzzer = PWM(Pin(25), freq=3000, duty=0)

# Globaler Alarm-Zustand
alarm_active = False

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
    global last_update_time, threshold, alarm_active
    while True:
        try:
            data, _ = udp.recvfrom(1024)
            json_data = ujson.loads(data)
            device_id = json_data.get("device_id")
            db_level = float(json_data.get("db_level", 0))

            if device_id in latest_data:
                # Aktuellen Wert speichern
                latest_data[device_id]["db_level"] = db_level
                update_display()
                save_log_entry(device_id, db_level)

                print(f"{device_id} meldet: {db_level:.1f} dB (Schwelle: {threshold} dB)")

                last_update_time = time.ticks_ms()
                set_wifi_icon(True)

                # Gemeinsame Alarmpruefung fuer beide Sensoren
                node1_db = latest_data["node1"]["db_level"]
                node2_db = latest_data["node2"]["db_level"]

                if node1_db > threshold or node2_db > threshold:
                    print("Alarm: Schwellenwert ueberschritten!")
                    show_alarm(True)
                    set_buzzer(True)
                    alarm_active = True
                else:
                    if alarm_active:
                        print("Alarm beendet – Werte wieder unter der Schwelle.")
                    show_alarm(False)
                    set_buzzer(False)
                    alarm_active = False

        except Exception as e:
            print("Fehler beim Empfang oder Verarbeiten:", e)


def monitor_connection():
    global last_update_time
    while True:
        if time.ticks_diff(time.ticks_ms(), last_update_time) > 10000:
            print("Keine Verbindung zu Sensoren")
            set_wifi_icon(False)
            show_alarm(False)
            set_buzzer(False)
        time.sleep(5)

def update_runtime_config(new_cfg):
    global threshold
    threshold = new_cfg.get("threshold", threshold)
    print("→ Laufzeitkonfiguration aktualisiert:", threshold)
    send_cmd(f'page03_t2.txt="{threshold} dB"')

def listen_for_button():
    global threshold, alarm_active
    send_cmd(f'page03_t2.txt="{threshold} dB"')
    print("Warte auf Touch Events vom Nextion Display ...")

    buffer = b""

    while True:
        if uart.any():
            buffer += uart.read()

            while b'\xff\xff\xff' in buffer:
                idx = buffer.index(b'\xff\xff\xff') + 3
                packet = buffer[:idx]
                buffer = buffer[idx:]

                print("Touch-Ereignis empfangen:", packet.hex())

                if packet.startswith(b'\x65\x02\x05\x01'):  # Minus
                    threshold = max(50, threshold - 1)
                    send_cmd(f'page03_t2.txt="{threshold} dB"')

                elif packet.startswith(b'\x65\x02\x06\x01'):  # Plus
                    threshold = min(120, threshold + 1)
                    send_cmd(f'page03_t2.txt="{threshold} dB"')

                elif packet.startswith(b'\x65\x02\x03\x01'):  # Speichern
                    save_config({"threshold": threshold})
                    print("Schwellenwert gespeichert:", threshold)

                elif packet.startswith(b'\x65\x01\x0A\x01'):  # Quittieren
                    print("Alarm quittiert")
                    set_buzzer(False)
                    show_alarm(False)

                elif packet.startswith(b'\x65\x00\x05\x01'):  # Zu page03
                    print("→ Navigation zu page03 erkannt")
                    time.sleep(0.15)
                    send_cmd(f'page03_t2.txt="{threshold} dB"')

                elif packet.startswith(b'\x65\x00\x04\x01'):  # Zu page02
                    print("→ Navigation zu page02 erkannt")
                    time.sleep(0.15)
                    dba = latest_data["node1"]["db_level"]
                    dbb = latest_data["node2"]["db_level"]

                    send_cmd(f'zHalleA.val={int(dba)}')
                    send_cmd(f'zHalleB.val={int(dbb)}')
                    send_cmd(f'page02_t0.txt="{dba:.1f} dB"')
                    send_cmd(f'page02_t1.txt="{dbb:.1f} dB"')

												 
                    show_alarm(alarm_active)

# Startsystem
last_update_time = time.ticks_ms()
ap = start_ap()
udp = setup_udp()

# Threads starten
_thread.start_new_thread(start_webserver, (lambda: latest_data, update_runtime_config))
_thread.start_new_thread(monitor_connection, ())
_thread.start_new_thread(listen_for_button, ())

udp_loop(udp)
