\# Pico 2W SCD41 Air Quality Monitor 2



Tämä projekti on kevyt ja itsenäinen ilmanlaadun seurantalaite, joka on toteutettu \*\*Raspberry Pi Pico 2W\*\* -kehitysalustalla ja \*\*SCD41\*\*-anturilla. Laite tallentaa mittaustulokset (CO2, lämpötila, kosteus) sisäiseen muistiin ja tarjoaa selainpohjaisen käyttöliittymän datan tarkasteluun.



\## Ominaisuudet

\- \*\*Reaaliaikainen seuranta:\*\* CO2 (ppm), Lämpötila (°C) ja Kosteus (%).

\- \*\*Datan tallennus:\*\* Tallentaa mittaukset 15 minuutin välein `data.csv`-tiedostoon (2 viikon historia).

\- \*\*Web-käyttöliittymä:\*\* Interaktiivinen Google Charts -graafi, jossa:

&#x20;   - Suodatus: 24h, 3pv, 7pv ja 14pv näkymät.

&#x20;   - Automaattinen \*\*Dark Mode\*\* -tuki.

&#x20;   - Päivän vaihtumisen osoittavat pystyviivat.

\- \*\*Vikasietoisuus:\*\* Automaattinen Wi-Fi-uudelleenkytkentä ja vuorokautinen NTP-aikasynkronointi.



\## Laitteisto

\- \*\*Raspberry Pi Pico 2W\*\* (tai Pico W)

\- \*\*Sensirion SCD41\*\* CO2-sensori (I2C-väylä)

\- Micro-USB-kaapeli virransyöttöön



\## Kytkennät

| SCD41 Pin | Pico 2W Pin | Tehtävä |

| :--- | :--- | :--- |

| \*\*VDD\*\* | \*\*3V3 (Pin 36)\*\* | Virransyöttö (3.3V) |

| \*\*GND\*\* | \*\*GND (Pin 38)\*\* | Maadoitus |

| \*\*SCL\*\* | \*\*GP5 (Pin 7)\*\* | I2C Clock |

| \*\*SDA\*\* | \*\*GP4 (Pin 6)\*\* | I2C Data |



\## Asennus

1\. Varmista, että Picoon on asennettu \*\*MicroPython\*\*-firmware.

2\. Luo tiedosto `wifi.py` ja lisää sinne verkkosi tiedot:

&#x20;  ```python

&#x20;  ssid = "VERKON\_NIMI"

&#x20;  password = "SALASANA"

&#x20;  ```

3\. Kopioi projektin pääkoodi tiedostoon `main.py` ja tallenna se Picoon.

4\. Käynnistä Pico. Laite tulostaa IP-osoitteen konsoliin, kun se on yhdistänyt verkkoon.

5\. Avaa selaimella Picon IP-osoite nähdäksesi graafit.



\## Käyttö

Graafi päivittyy automaattisesti taustalla. Voit vaihtaa aikaväliä yläreunan painikkeilla. Jos sähköt katkeavat, laite lataa aiemman historian automaattisesti tiedostosta käynnistyksen yhteydessä.

