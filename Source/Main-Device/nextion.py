from machine import UART
import time

# UART1 fuer Nextion Display
uart = UART(1, baudrate=9600, tx=16, rx=17)

DEBUG = False  # Auf True setzen, um gesendete Kommandos auszugeben

def send_cmd(cmd):
    """Sende generierten Befehl an Nextion Display"""
    if DEBUG:
        print("SEND:", cmd)
    uart.write(cmd.encode())
    uart.write(b'\xff\xff\xff')  # Befehl-Endesequenz
    time.sleep_ms(30)  # Kurze Pause fuer Stabilitaet

def display_value(device_id, db_level):
    """Zeigt dB-Wert im jeweiligen Messgeraet an (Halle A oder B)"""
    if db_level is None:
        if device_id == "node1":
            send_cmd('page02_t0.txt="Kein Messwert!"')
            send_cmd('zHalleA.val=0')
            send_cmd('ref zHalleA')
        elif device_id == "node2":
            send_cmd('page02_t1.txt="Kein Messwert!"')
            send_cmd('zHalleB.val=0')
            send_cmd('ref zHalleB')
        return

    min_db = 0
    max_db = 120

    # Begrenzen auf gueltigen Wertebereich
    db_level = max(min_db, min(db_level, max_db))

    val = int((db_level - min_db) / (max_db - min_db) * 180)
    val = max(0, min(val, 180))  # Begrenzung auf 0–180 Grad

    if device_id == "node1":
        value_txt = "Halle A: {:.1f} dB".format(db_level)
        send_cmd(f'page02_t0.txt="{value_txt}"')
        send_cmd(f'zHalleA.val={val}')
        send_cmd('ref zHalleA')  # Erzwingt Redraw
    elif device_id == "node2":
        value_txt = "Halle B: {:.1f} dB".format(db_level)
        send_cmd(f'page02_t1.txt="{value_txt}"')
        send_cmd(f'zHalleB.val={val}')
        send_cmd('ref zHalleB')

def set_wifi_icon(active):
    """Aktualisiert WiFi-Symbol (0 = verbunden, 1 = getrennt)"""
    if active:
        send_cmd('pWiFi.pic=0')
    else:
        send_cmd('pWiFi.pic=1')

def show_alarm(active):
    """Zeigt/Versteckt Alarmanzeige auf Seite 2"""
    if active:
        send_cmd('vis page02_p0,1')
        send_cmd('vis page02_b1,1')
    else:
        send_cmd('vis page02_p0,0')
        send_cmd('vis page02_b1,0')