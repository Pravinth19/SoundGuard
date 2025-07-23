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

```
C:/SoundGuard/Source/Main-Device/
│
├── main.py                → Zentrale Steuerung (UDP-Empfang, Alarmlogik, Buzzer, Threads)
├── web_config.py          → HTTP-Webserver mit REST-Endpunkten für Konfig, Logs, UI
├── nextion.py             → Steuerung des Nextion-Displays via UART
│
├── index.html             → Web-Oberfläche: Schwellenwert einstellen, Live-Daten, Logs öffnen
├── logs.html              → Web-Loganzeige mit CSV-Download und Löschen
├── soundguard_logo.webp   → Webinterface-Logo
│
├── config.json            → 🛠️ Automatisch generiert: Schwellenwertkonfiguration
├── log.txt                → 🛠️ Automatisch generiert: Messwert-Logfile (max. 50 Einträge, FIFO)
│
└── [optional]
    └── log.csv            → 📥 Dynamisch generiert bei Downloadanfrage (nicht persistent gespeichert)


```

---

## 📂 Schritt 5: Projektdateien auf ESP32 kopieren

### 📦 Dateien auf den ESP32 übertragen:
Alle Dateien müssen einzeln auf den ESP32 kopiert werden. Verwende dazu folgenden Befehl (jeweils anpassen):

```bash
mpremote connect COM3 cp main.py :
mpremote connect COM3 cp web_config.py :
mpremote connect COM3 cp nextion.py :
mpremote connect COM3 cp index.html :
mpremote connect COM3 cp logs.html :
mpremote connect COM3 cp soundguard_logo.webp :

```
💡 Hinweise:

- Ersetze COM3 ggf. mit dem tatsächlichen COM-Port deines ESP32.
- Achte darauf, dass sich alle Dateien im aktuellen Arbeitsverzeichnis befinden.

---

## ✅ Schritt 6: Testen der Weboberfläche von SoundGuard

---

### 🔌 1. ESP32 starten

```bash
mpremote run main.py
```

---

### 📶 2. Mit WLAN des ESP32 verbinden

Verbinde deinen Laptop oder Smartphone mit folgendem Netzwerk:

```
SSID:     Master  
Passwort: password
```

> 🔒 Das WLAN wird vom ESP32 als Access Point bereitgestellt (siehe `main.py`).

---

### 🌐 3. Webinterface im Browser öffnen

Öffne im Browser:

```
http://192.168.4.1
```

Du solltest nun Folgendes sehen:

- ✅ SoundGuard Logo  
- ✅ Eingabefeld für Alarm-Schwellenwert  
- ✅ „Logs anzeigen“-Button  
- ✅ Live-Datenanzeige („Messgerät Halle A/B“)

---

### ⚙️ 4. Webinterface-Funktionen testen

#### ✅ Schwellenwert setzen

1. Gib einen Wert zwischen **50–120 dB** ein  
2. Klicke auf **„Speichern“**  
3. ✅ Popup erscheint: „Konfiguration gespeichert“

Der Wert wird:

- in `config.json` gespeichert  
- sofort an Sensor-Nodes gesendet  
- auf dem Display angezeigt

---

#### 🔁 Live-Daten prüfen

- Live-Werte von `node1` und `node2` werden **alle 2 Sekunden aktualisiert**
- Alternativ direkt im Browser prüfen:
  ```
  http://192.168.4.1/data
  ```
  Beispiel-Antwort (JSON):
  ```json
  {
    "node1": { "device_id": "node1", "db_level": 83.4 },
    "node2": { "device_id": "node2", "db_level": 76.1 }
  }
  ```

---

#### 📄 Logs anzeigen & verwalten

1. Klicke im Webinterface auf **„Logs anzeigen“**
2. Es öffnet sich `/logs.html` mit:

- 🔍 Tabelle mit Zeit, Sensor, Dezibelwert  
- 📥 CSV-Download-Button  
- 🗑️ Button zum Löschen der Logs

---

### 🔗 Manuelle Endpunkte (optional)

| Funktion              | URL                                       |
|-----------------------|--------------------------------------------|
| Webinterface          | http://192.168.4.1/index.html              |
| Live-Daten (JSON)     | http://192.168.4.1/data                    |
| Logs anzeigen (raw)   | http://192.168.4.1/log                     |
| Logs als CSV          | http://192.168.4.1/log.csv                 |
| Logs löschen          | http://192.168.4.1/log/delete              |
| Logs als HTML-Tabelle | http://192.168.4.1/logs.html              |

> ℹ️ Hinweis: Es werden **max. 50 Einträge** gespeichert. Danach wird das Log automatisch geleert (`log.txt` wird überschrieben).

---