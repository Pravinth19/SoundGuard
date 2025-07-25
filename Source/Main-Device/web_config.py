import socket
import ujson
import time
from nextion import set_wifi_icon  

CONFIG_FILE = "config.json"

# Konfiguration aus Datei laden
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            cfg = ujson.load(f)
            print("-> Geladene Konfiguration:", cfg)
            return cfg
    except:
        print("-> Keine Konfiguration gefunden, nutze Standardwert.")
        return {"threshold": 85}

# Konfiguration in Datei speichern
def save_config(new_cfg):
    print("-> Speichere Konfiguration:", new_cfg)
    with open(CONFIG_FILE, "w") as f:
        ujson.dump(new_cfg, f)
        f.flush()
    time.sleep(0.1)  # kurze Verzoegerung fuer Dateisystem

# Startet einfachen HTTP-Webserver auf Port 80
def start_webserver(get_live_data, on_config_change=None):
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    try:
        s.bind(addr)
    except OSError as e:
        print("Fehler: Port 80 ist bereits belegt – vermutlich laeuft der Webserver noch.")
        set_wifi_icon(False)  # WiFi-Symbol auf Display deaktivieren
        return
    s.listen(1)
    print("Webserver laeuft auf http://192.168.4.1")
    set_wifi_icon(True)  # WiFi-Symbol aktivieren

    while True:
        cl, _ = s.accept()
        try:
            raw = cl.recv(1024)
            if not raw:
                continue
            req = raw.decode()

            # API-Endpunkte
            if "GET /data" in req:
                # Sensor-Daten als JSON liefern
                data = get_live_data()
                cl.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" + ujson.dumps(data))

            elif "POST /config" in req:
                # Konfiguration aktualisieren (z. B. Schwellenwert)
                try:
                    body = req.split("\r\n\r\n", 1)[1]
                    value_str = body.split("=", 1)[1]
                    cfg = {"threshold": int(value_str)}
                    save_config(cfg)
                    if on_config_change:
                        on_config_change(cfg)
                    cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nKonfiguration gespeichert.")
                except Exception as e:
                    print("-> Fehler beim Parsen:", e)
                    cl.send("HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nFehlerhafte Eingabe.")

            elif "GET /index.html" in req or "GET / " in req:
                # Hauptseite anzeigen
                try:
                    with open("index.html", "r") as f:
                        cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                        cl.send(f.read())
                except:
                    cl.send("HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nindex.html nicht gefunden.")

            elif "GET /logs.html" in req:
                # Log-Anzeige-Seite
                try:
                    with open("logs.html", "r") as f:
                        cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                        cl.send(f.read())
                except:
                    cl.send("HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nlogs.html fehlt.")

            elif "GET /soundguard_logo.webp" in req:
                # Logo-Bild laden
                try:
                    with open("soundguard_logo.webp", "rb") as f:
                        cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: image/webp\r\n\r\n")
                        cl.send(f.read())
                except:
                    cl.send("HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nLogo fehlt.")

            elif "GET /log/delete" in req:
                # Logs loeschen
                try:
                    with open("log.txt", "w") as f:
                        f.write("")
                    cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nLogs geloescht.")
                except:
                    cl.send("HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nFehler beim Loeschen.")

            elif "GET /log" in req:
                # Rohdaten aus Log anzeigen
                try:
                    with open("log.txt", "r") as f:
                        log_content = f.read()
                    cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n" + log_content)
                except:
                    cl.send("HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nKeine Logs vorhanden.")

            elif "GET /log.csv" in req:
                # Log als CSV-Datei herunterladen
                try:
                    with open("log.txt", "r") as f:
                        content = f.read()
                    csv = "Zeit;Sensor;dB\n" + content.replace(" dB", "").replace(",", ";")
                    cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/csv\r\nContent-Disposition: attachment; filename=log.csv\r\n\r\n" + csv)
                except:
                    cl.send("HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nKeine Logs vorhanden.")

            else:
                # Fallback-Seite mit Uebersicht der verfuegbaren Endpunkte
                html = """<html><body><h3>SoundGuard Webserver</h3>
                          <p>Verfuegbare Endpunkte:</p>
                          <ul>
                            <li><a href="/index.html">index.html</a></li>
                            <li><a href="/logs.html">logs.html</a></li>
                            <li><a href="/log">Log ansehen</a></li>
                            <li><a href="/log/delete">Log loeschen</a></li>
                            <li><a href="/log.csv">Log als CSV</a></li>
                          </ul></body></html>"""
                cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html)

        except Exception as e:
            print("Webserver-Fehler:", e)

        finally:
            cl.close()
            time.sleep(0.01)  # kleine Pause, um CPU zu entlasten
