from machine import UART
import time

uart = UART(1, baudrate=9600, tx=17, rx=16)

def send_cmd(cmd):
    uart.write(cmd.encode())
    uart.write(b'\xff\xff\xff')  # Endbefehl für Nextion

def display_value(device_id, db_level):
    send_cmd(f't0.txt="{device_id}"')
    send_cmd(f't1.txt="{db_level} dB"')
