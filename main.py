import network
import socket
import time
import machine
import ntptime
import os
from wifi import ssid, password

# --- ASETUKSET ---
SSID = ssid
PASSWORD = password
MEASURE_INTERVAL = 900     # 15 minuuttia
MAX_HISTORY = 1344         # 2 viikkoa
NTP_SYNC_INTERVAL = 86400  # 24 tuntia

def get_utc_offset():
    t = time.localtime()
    month, day = t[1], t[2]
    if 3 < month < 10 or (month == 3 and day >= 29) or (month == 10 and day < 25):
        return 3 * 3600 # Kesäaika
    return 2 * 3600     # Talviaika

# --- TIEDOSTONHALLINTA ---
def save_to_file(entry):
    try:
        with open('data.csv', 'a') as f:
            f.write(f"{entry[0]},{entry[1]},{entry[2]},{entry[3]}\n")
    except: pass

def load_from_file():
    history = []
    try:
        with open('data.csv', 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 4:
                    history.append([parts[0], int(parts[1]), float(parts[2]), float(parts[3])])
    except: pass
    return history[-MAX_HISTORY:] if history else []

def prune_file(history):
    try:
        with open('data.csv', 'w') as f:
            for entry in history:
                f.write(f"{entry[0]},{entry[1]},{entry[2]},{entry[3]}\n")
    except: pass

# --- SCD41 AJURI ---
class SCD4X:
    def __init__(self, i2c, addr=0x62):
        self.i2c = i2c
        self.addr = addr
        time.sleep(2)
        try:
            self.i2c.writeto(self.addr, b'\x3f\x86')
            time.sleep(0.5)
        except: pass

    def start_periodic_measurement(self):
        self.i2c.writeto(self.addr, b'\x21\xb1')

    def read_measurement(self):
        self.i2c.writeto(self.addr, b'\xec\x05')
        time.sleep(0.01)
        data = self.i2c.readfrom(self.addr, 9)
        co2 = (data[0] << 8) | data[1]
        temp = -45 + 175 * ((data[3] << 8) | data[4]) / 65536
        humi = 100 * ((data[6] << 8) | data[7]) / 65536
        return co2, temp, humi

# --- HTML & JS ---
def generate_html(history):
    rows_list = []
    prev_day = None
    for e in history:
        # e[0] on muodossa "DD.MM. HH:MM"
        parts = e[0].split(" ")
        if len(parts) == 2:
            date_part, time_part = parts
        else:
            date_part, time_part = "", e[0]
            
        # Tarkistetaan vaihtuuko päivä
        if prev_day is not None and date_part != prev_day:
            annot = f"'{date_part}'" # Lisätään päivämäärä pystyviivan tekstiksi
        else:
            annot = "null"
        prev_day = date_part
        
        rows_list.append(f"['{time_part}', {annot}, {e[1]}, {e[2]}, {e[3]}, 1000]")
        
    rows = ",".join(rows_list)
    
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SCD41 Monitori</title>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <style>
        :root {{ --bg: #ffffff; --text: #333; --card: #f9f9f9; }}
        @media (prefers-color-scheme: dark) {{
            :root {{ --bg: #121212; --text: #e0e0e0; --card: #1e1e1e; }}
        }}
        body {{ font-family: sans-serif; background: var(--bg); color: var(--text); text-align: center; margin: 0; }}
        .btn-group {{ margin: 20px; }}
        button {{ padding: 10px 20px; margin: 5px; cursor: pointer; border: none; border-radius: 5px; background: #007bff; color: white; }}
        button:active {{ opacity: 0.8; }}
        #chart {{ width: 100%; height: 500px; }}
    </style>
    <script>
      google.charts.load('current', {{'packages':['corechart']}});
      var fullData = [{rows}];
      function draw(limit) {{
        var displayData = limit > 0 ? fullData.slice(-limit) : fullData;
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'Aika');
        data.addColumn({{type: 'string', role: 'annotation'}}); // Päivän vaihtumisen viiva
        data.addColumn('number', 'CO2 (ppm)');
        data.addColumn('number', 'Lämpö (C)');
        data.addColumn('number', 'Kosteus (%)');
        data.addColumn('number', 'Suositusraja');
        data.addRows(displayData);

        var isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        var opt = {{
          focusTarget: 'category', curveType: 'function', backgroundColor: 'transparent',
          legend: {{ position: 'bottom', textStyle: {{ color: isDark ? '#ccc' : '#333' }} }},
          chartArea: {{ width: '85%', height: '70%' }},
          annotations: {{ style: 'line', textStyle: {{ color: isDark ? '#aaa' : '#555', fontSize: 11 }} }},
          vAxes: {{ 
            0: {{ title: 'CO2 (ppm)', textStyle: {{color: isDark ? '#aaa' : '#333'}}, gridlines: {{count: 5, color: isDark ? '#333' : '#eee'}} }}, 
            1: {{ title: 'Lämpö (C)', textStyle: {{color: isDark ? '#aaa' : '#333'}}, gridlines: {{color: 'transparent'}} }},
            2: {{ textPosition: 'none', gridlines: {{color: 'transparent'}} }} // Kosteus omalla akselilla ilman häiritseviä viivoja
          }},
          series: {{ 
            0: {{ targetAxisIndex: 0, color: '#4285F4' }}, 
            1: {{ targetAxisIndex: 1, color: '#DB4437' }}, 
            2: {{ targetAxisIndex: 2, color: '#F4B400' }},
            3: {{ targetAxisIndex: 0, color: '#888', lineDashStyle: [4, 4], visibleInLegend: false, tooltip: false }}
          }},
          hAxis: {{ slantedText: false, textStyle: {{color: isDark ? '#aaa' : '#333'}} }}
        }};
        new google.visualization.LineChart(document.getElementById('chart')).draw(data, opt);
      }}
      google.charts.setOnLoadCallback(() => draw(96)); // Oletus 24h
    </script>
    </head><body>
        <h1>Ilmanlaatu</h1>
        <div class="btn-group">
            <button onclick="draw(96)">24h</button>
            <button onclick="draw(288)">3pv</button>
            <button onclick="draw(672)">7pv</button>
            <button onclick="draw(0)">14pv</button>
        </div>
        <div id="chart"></div>
    </body></html>"""

# --- APUFUNKTIOT ---
def connect_wifi():
    wlan.connect(SSID, PASSWORD)
    print("Yhdistetään Wi-Fiin...")
    for _ in range(10):
        if wlan.isconnected():
            print("Yhteys palautettu:", wlan.ifconfig()[0])
            return True
        time.sleep(1)
    return False

def sync_ntp():
    for server in ["0.fi.pool.ntp.org", "time.google.com"]:
        try:
            ntptime.host = server
            ntptime.settime()
            return True
        except: pass
    return False

# --- ALUSTUS ---
data_history = load_from_file()
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
connect_wifi()

sync_ntp()
i2c = machine.I2C(0, sda=machine.Pin(4), scl=machine.Pin(5), freq=100000)
sensor = SCD4X(i2c)
sensor.start_periodic_measurement()

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 80))
s.listen(5)
s.settimeout(0.1)

last_measure, last_ntp_sync = 0, time.time()
first_run = True

while True:
    now = time.time()
    
    if not wlan.isconnected():
        connect_wifi()

    if now - last_ntp_sync >= NTP_SYNC_INTERVAL:
        if sync_ntp(): last_ntp_sync = now

    if first_run or (now - last_measure >= MEASURE_INTERVAL):
        try:
            co2, temp, humi = sensor.read_measurement()
            t = time.localtime(time.time() + get_utc_offset())
            ts = "{:02d}.{:02d}. {:02d}:{:02d}".format(t[2], t[1], t[3], t[4])
            
            new_entry = [ts, co2, round(temp,1), round(humi,1)]
            data_history.append(new_entry)
            save_to_file(new_entry)
            
            if len(data_history) > MAX_HISTORY:
                data_history.pop(0)
                if now - last_ntp_sync < 1000: prune_file(data_history)
            
            print(f"[{ts}] CO2: {co2} ppm, Lämpö: {temp:.1f} C, Kosteus: {humi:.1f} %")
            last_measure, first_run = now, False
        except:
            last_measure = now - MEASURE_INTERVAL + 10 

    try:
        cl, addr = s.accept()
        try:
            cl.settimeout(1.0)
            request = cl.recv(1024)
            cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
            cl.sendall(generate_html(data_history))
        finally:
            cl.close()
    except OSError: pass

    time.sleep(0.1)
