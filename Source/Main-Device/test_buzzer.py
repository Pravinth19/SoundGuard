from machine import Pin, PWM
import time

# Buzzer auf GPIO25 initialisieren
buzzer = PWM(Pin(25))
buzzer.freq(3000)  # Frequenz in Hz (z. B. 3000 Hz = 3 kHz)

# Ton aktivieren
buzzer.duty(512)  # 50% Duty Cycle

print("Buzzer sollte jetzt piepen...")

# 1 Sekunden Ton
time.sleep(2)

# Ton aus
buzzer.duty(0)
buzzer.deinit()

print("Test beendet.")
