from machine import UART
import time

uart = UART(1, baudrate=9600, tx=17, rx=16)

def send_cmd(cmd):
    uart.write(cmd.encode())
    uart.write(b'\xff\xff\xff')

def display_value(device_id, db_level):
    min_db = 50
    max_db = 120

    value_txt = "{:.1f} dB".format(db_level)
    val = int((db_level - min_db) / (max_db - min_db) * 180)
    val = max(0, min(val, 180))  # Begrenzung auf gültigen Bereich

    if device_id == "node1":
        send_cmd(f't0.txt="{value_txt}"')
        send_cmd(f'zHalleA.val={val}')
    elif device_id == "node2":
        send_cmd(f't1.txt="{value_txt}"')
        send_cmd(f'zHalleB.val={val}')


def display_status(msg):
    send_cmd(f'status.txt="{msg}"')

def set_wifi_icon(active):
    if active:
        send_cmd("pWiFi.pic=1")
    else:
        send_cmd("pWiFi.pic=0")

def show_alarm(active):
    if active:
        send_cmd("p0.vis=1")
        send_cmd("t4.vis=1")
    else:
        send_cmd("p0.vis=0")
        send_cmd("t4.vis=0")

