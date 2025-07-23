from machine import UART
import time

# Initialisierung von UART1 fuer die Kommunikation mit dem Nextion Display
# TX = GPIO16, RX = GPIO17, Baudrate 9600
uart = UART(1, baudrate=9600, tx=16, rx=17)

DEBUG = False  # Fuer Debugzwecke: True zeigt alle gesendeten Befehle

def send_cmd(cmd):
    """
    Sendet einen Befehl an das Nextion Display.
    Anhaengen von drei 0xFF Bytes ist zwingend erforderlich fuer das Nextion-Protokoll.
    """
    if DEBUG:
        print("SEND:", cmd)
    uart.write(cmd.encode())
    uart.write(b'\xff\xff\xff')  # Befehl-Endesequenz laut Nextion-Protokoll
    time.sleep_ms(30)  			 # kurze Pause fuer Display-Stabilitaet

def display_value(device_id, db_level):
    """
    Zeigt den Dezibelwert fuer das jeweilige Messgeraet auf Seite 2 des Displays an.
    Visualisiert den Wert als Text und ueber einen Drehwinkel (0–180).
    """
    if db_level is None:
        # Kein Wert erhalten → Fehleranzeige
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

    # Werte begrenzen und umrechnen auf 0–180
    db_level = max(min_db, min(db_level, max_db))
    val = int((db_level - min_db) / (max_db - min_db) * 180)
    val = max(0, min(val, 180))

    if device_id == "node1":
        value_txt = "Halle A: {:.1f} dB".format(db_level)
        send_cmd(f'page02_t0.txt="{value_txt}"')
        send_cmd(f'zHalleA.val={val}')
        send_cmd('ref zHalleA')
    elif device_id == "node2":
        value_txt = "Halle B: {:.1f} dB".format(db_level)
        send_cmd(f'page02_t1.txt="{value_txt}"')
        send_cmd(f'zHalleB.val={val}')
        send_cmd('ref zHalleB')

def set_wifi_icon(active):
    """
    Aendert das WiFi-Symbol basierend auf Verbindungsstatus:
    pic=0 → verbunden, pic=1 → getrennt
    """
    if active:
        send_cmd('pWiFi.pic=0')
    else:
        send_cmd('pWiFi.pic=1')

def show_alarm(active):
    """
    Zeigt oder versteckt die Alarmanzeige auf Seite 2.
    Sichtbarkeit Warndreieck (p0) und einen Button (b1) steuern.
    """
    if active:
        send_cmd('vis page02_p0,1')  # Warndreieck sichtbar
        send_cmd('vis page02_b1,1')  # Quittierbutton sichtbar
    else:
        send_cmd('vis page02_p0,0')
        send_cmd('vis page02_b1,0')
