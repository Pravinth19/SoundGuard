from machine import UART
import time

# UART1: TX=17, RX=16
uart = UART(1, baudrate=9600, tx=16, rx=17)

# Direkt Befehl senden (kein send_cmd!)
uart.write(b't0.txt="Direkt"\xff\xff\xff')

print("Direktbefehl gesendet")