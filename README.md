# Inbetriebnahme Hauptgerät ESP32 mit MicroPython 
## 🧰 Voraussetzungen

- **VSCode** ist bereits installiert ✅
- Du besitzt einen **ESP32** Mikrocontroller ✅
- **USB-Kabel** zur Verbindung mit dem Computer
- **Internetverbindung** zur Installation von Tools

---

## 🔧 Schritt 1: Treiber (falls nötig) installieren

Falls dein ESP32 nicht erkannt wird:

1. Lade den CP210x Treiber herunter:
2. Installiere den Treiber:
    - CP210x Treiber (Silicon Labs)

---

## 💻 Schritt 2: MicroPython Firmware auf den ESP32 flashen

### 🔹 A. `esptool.py` installieren

Öffne ein Terminal oder die Eingabeaufforderung als **Administrator**:

```bash
pip install esptool
```

### 🔹 B. COM-Port herausfinden

Stecke den ESP32 ein und finde den COM-Port:

- Windows: Gerätemanager → Anschlüsse (COM & LPT)

### 🔹 C. ESP32 löschen (optional, aber empfohlen)

```bash
esptool --port COMx erase_flash
```

*Ersetze `COMx` mit dem richtigen Port.*

### 🔹 D. Firmware herunterladen

Lade die aktuelle Firmware von https://micropython.org/download/esp32/

Aktuelle Firmware (Stand 24.06.2025): [**v1.25.0 (2025-04-15) .bin**](https://micropython.org/resources/firmware/ESP32_GENERIC-20250415-v1.25.0.bin)

### 🔹 E. Firmware flashen

Bsp. ESP32 ist am COM Port 3 verbunden

```bash
esptool --chip esp32 --port COM3 write_flash -z 0x1000 ESP32_GENERIC-20250415-v1.25.0.bin
```


![image](https://github.com/user-attachments/assets/1772f6fd-2b8e-4670-b387-e065990693a6)

Frimware erfolgreich geladen.

---

## 💻 Schritt 3: **`mpremote` installieren**

Öffne dein Terminal (z. B. `cmd` unter Windows) und gib ein:

```bash
pip install mpremote
```

---

## 📝 Schritt 4: **Testen, ob `mpremote` funktioniert**

```bash
mpremote --help
```

Wenn du eine Liste von Befehlen siehst, ist alles korrekt installiert.

---

## Projektordner Übersicht

📂 Pfad:
C:/SoundGuard/Source/Main-Device/

## 📄 Struktur:

```plaintext
C:/SoundGuard/Source/Main-Device/
│
├── main.py              → zentrale Steuerung des Systems
├── web_config.py        → Webserver, Konfiguration & REST-API
├── nextion.py           → Displaysteuerung (z. B. Nextion-Anzeige)
│
├── index.html           → Webinterface für Konfiguration & Live-Daten
├── soundguard_logo.webp → Logo für das Webinterface
├── config.json          → automatisch erzeugte Konfigurationsdatei (Grenzwert)
```
---

## 📂 Schritt 5: Projektdateien auf ESP32 kopieren

### 📦 Dateien auf den ESP32 übertragen:

```bash
mpremote connect COM3 cp main.py :
mpremote connect COM3 cp web_config.py :
mpremote connect COM3 cp nextion.py :
mpremote connect COM3 cp index.html :
mpremote connect COM3 cp soundguard_logo.webp :
```

---

## ✅ Schritt 6: Testen der Weboberfläche

### 1. Starte ESP32:

```bash
mpremote run main.py
```

### 2. Verbinde Laptop mit WLAN:

```
SSID: Master
Passwort: password
```

### 3. Öffne Browser:

```
http://192.168.4.1
```

➡ Du siehst die Konfigurationsseite

➡ Speicher einen Schwellenwert

➡ Prüfe unter `/data`, ob Live-Daten ankommen



