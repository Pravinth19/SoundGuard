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
    "node1": {"device_id": "node1", "db_level": None},
    "node2": {"device_id": "node2", "db_level": None}
}

# Zeitstempel pro Node
last_update_times = {
    "node1": time.ticks_ms(),
    "node2": time.ticks_ms()
}

# Buzzer Setup
buzzer = PWM(Pin(25), freq=2500, duty=0)

# Globaler Alarm-Zustand
alarm_active = False
quittiert_bis = 0  # Zeitstempel bis wann der Buzzer aus ist

# Aktuell angezeigte Seite auf dem Display (1 = Menu, 2 = Live-Daten, 3 = Schwellenwert)
current_page = 1

def set_buzzer(active):
    global quittiert_bis
    if time.ticks_ms() < quittiert_bis:
        buzzer.duty(0)
        return
    if active:
        buzzer.freq(2500)
        buzzer.duty(512)
        time.sleep(0.5)
        buzzer.deint()
					   
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

def save_log_entry(device_id, db_level):
    try:
        timestamp = time.localtime()
        timestr = "{:02d}:{:02d}:{:02d}".format(timestamp[3], timestamp[4], timestamp[5])
        with open("log.txt", "a") as f:
            f.write(f"{timestr},{device_id},{db_level:.1f} dB\n")
        check_and_clear_logs()
    except Exception as e:
        print("Fehler beim Log-Speichern:", e)

MAX_LOG_ENTRIES = 50

def check_and_clear_logs():
    try:
        with open("log.txt", "r") as f:
            lines = f.readlines()
        if len(lines) >= MAX_LOG_ENTRIES:
            print("→ Loggrenze erreicht. Logdateien werden geloescht.")
            with open("log.txt", "w") as f:
                f.write("") 	# leeren
    except Exception as e:
        print("Fehler beim Ueberpruefen/Loeschen der Logs:", e)

def udp_loop(udp):
    global threshold, alarm_active, current_page
    while True:
        try:
            data, _ = udp.recvfrom(1024)
            json_data = ujson.loads(data)
            device_id = json_data.get("device_id")
            db_level = float(json_data.get("db_level", 0))

            if device_id in latest_data:
                latest_data[device_id]["db_level"] = db_level
                last_update_times[device_id] = time.ticks_ms()

                display_value(device_id, db_level)
                save_log_entry(device_id, db_level)

                print(f"{device_id} meldet: {db_level:.1f} dB (Schwelle: {threshold} dB)")

                node1_db = latest_data["node1"]["db_level"]
                node2_db = latest_data["node2"]["db_level"]

                if node1_db and node1_db > threshold or node2_db and node2_db > threshold:
                    print("Alarm: Schwellenwert ueberschritten!")
                    show_alarm(True)
                    set_buzzer(True)
                    alarm_active = True
                else:
                    if alarm_active:
                        print("Alarm beendet - Werte wieder unter der Schwelle.")
                    show_alarm(False)
                    set_buzzer(False)
                    alarm_active = False

        except Exception as e:
            print("Fehler beim Empfang oder Verarbeiten:", e)

def monitor_connection():
    while True:
        now = time.ticks_ms()
        for node in ["node1", "node2"]:
            if time.ticks_diff(now, last_update_times[node]) > 10000:
                print(f"Keine Verbindung zu {node}")
                display_value(node, None)	# Zeigt "Kein Messwert!" im Display an
        time.sleep(5)

def update_runtime_config(new_cfg):
    global threshold
    threshold = new_cfg.get("threshold", threshold)
    print("→ Laufzeitkonfiguration aktualisiert:", threshold)
    send_cmd(f'page03_t2.txt="{threshold} dB"')

									
    send_threshold_to_nodes(threshold)

def send_threshold_to_nodes(value):
    msg = ujson.dumps({"threshold": value})
    node_addresses = [
        ("192.168.4.101", 4211),	# SensorNode 1
        ("192.168.4.102", 4212)		# SensorNode 2 (optional)
    ]
 
    try:
        udp_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
 
        for ip, port in node_addresses:
            udp_send.sendto(msg.encode(), (ip, port))
            print(f"Schwellenwert an {ip}:{port} gesendet.")
 
        udp_send.close()
    except Exception as e:
        print("Fehler beim Senden:", e)

def send_quittierung_to_nodes():
    msg = ujson.dumps({"quittiert": True})
    node_addresses = [
        ("192.168.4.101", 4211),
        ("192.168.4.102", 4212)
    ]
    try:
        udp_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        for ip, port in node_addresses:
            udp_send.sendto(msg.encode(), (ip, port))
            print(f"Quittierung an {ip}:{port} gesendet.")
        udp_send.close()
    except Exception as e:
        print("Fehler beim Senden der Quittierung:", e)

def listen_for_button():
    global threshold, alarm_active, current_page, quittiert_bis
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

                if packet.startswith(b'\x66') and len(packet) >= 4:
                    current_page = packet[1]
                    print("→ Aktive Seite:", current_page)

                elif packet.startswith(b'\x65\x02\x05\x01'):  # Minus
                    threshold = max(50, threshold - 1)
                    send_cmd(f'page03_t2.txt="{threshold} dB"')

                elif packet.startswith(b'\x65\x02\x06\x01'):  # Plus
                    threshold = min(120, threshold + 1)
                    send_cmd(f'page03_t2.txt="{threshold} dB"')

                elif packet.startswith(b'\x65\x02\x03\x01'):  # Speichern
                    cfg = {"threshold": threshold}
                    save_config(cfg)
                    update_runtime_config(cfg)
                    print("Schwellenwert gespeichert & an Nodes gesendet:", threshold)

                elif packet.startswith(b'\x65\x01\x05\x01'):  # Quittieren
                    print("Alarm quittiert")
                    quittiert_bis = time.ticks_add(time.ticks_ms(), 60000)
                    set_buzzer(False)
                    show_alarm(False)
                    send_quittierung_to_nodes()

                elif packet.startswith(b'\x65\x00\x04\x01'):  # zu page02 (Live-Daten)
                    print("→ Navigation zu page02 erkannt")
                    time.sleep(0.15)
                    display_value("node1", latest_data["node1"]["db_level"])
                    display_value("node2", latest_data["node2"]["db_level"])
                    show_alarm(alarm_active)

                elif packet.startswith(b'\x65\x00\x05\x01'):  # zu page03 (Einstellungen)
                    print("→ Navigation zu page03 erkannt")
                    time.sleep(0.15)
                    send_cmd(f'page03_t2.txt="{threshold} dB"')

# Startsystem
ap = start_ap()
udp = setup_udp()

# Threads starten
_thread.start_new_thread(start_webserver, (lambda: latest_data, update_runtime_config))
_thread.start_new_thread(monitor_connection, ())
_thread.start_new_thread(listen_for_button, ())

udp_loop(udp)
