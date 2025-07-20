from machine import UART
import time

# UART1 für Nextion Display (TX=16, RX=17)
uart = UART(1, baudrate=9600, tx=16, rx=17)

def send_cmd(cmd):
    """Sende generierten Befehl an Nextion Display"""
    uart.write(cmd.encode())
    uart.write(b'\xff\xff\xff')  # Befehl-Endesequenz

def display_value(device_id, db_level):
    """Zeigt dB-Wert im jeweiligen Messgerät an (Halle A oder B)"""
    min_db = 50
    max_db = 120

    value_txt = "{:.1f} dB".format(db_level)
    val = int((db_level - min_db) / (max_db - min_db) * 180)
    val = max(0, min(val, 180))  # Begrenzung auf 0–180 Grad

    if device_id == "node1":
        send_cmd(f'page02_t0.txt="{value_txt}"')
        send_cmd(f'zHalleA.val={val}')
    elif device_id == "node2":
        send_cmd(f'page02_t1.txt="{value_txt}"')
        send_cmd(f'zHalleB.val={val}')

def set_wifi_icon(active):
    """Aktualisiert WiFi-Symbol (1 = verbunden, 0 = getrennt)"""
    if active:
        send_cmd("pWiFi.pic=1")  # ID 8 auf beiden Seiten
    else:
        send_cmd("pWiFi.pic=0")

def show_alarm(active):
    """Zeigt/Versteckt Alarmanzeige"""
    if active:
        send_cmd("page02_p0.vis=1")  # Warnsymbol (Dreieck)
        send_cmd("page02_b1.vis=1")  # Button "Bitte quittieren"
    else:
        send_cmd("page02_p0.vis=0")
        send_cmd("page02_b1.vis=0")
