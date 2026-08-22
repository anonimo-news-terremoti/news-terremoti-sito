import json
import math
import requests
from datetime import datetime, timedelta, timezone

# Centro approssimativo + limiti geografici della regione
REGIONI = {
    "VDA": ("Valle d'Aosta", 45.74, 7.32, (45.45, 46.10, 6.70, 7.95)),
    "PIE": ("Piemonte", 45.05, 7.67, (44.00, 46.50, 6.60, 9.20)),
    "LIG": ("Liguria", 44.40, 8.93, (43.70, 44.80, 7.40, 10.10)),
    "LOM": ("Lombardia", 45.47, 9.19, (44.70, 46.65, 8.40, 11.45)),
    "TAA": ("Trentino-Alto Adige", 46.50, 11.35, (45.65, 47.20, 10.35, 12.55)),
    "VEN": ("Veneto", 45.44, 12.33, (44.75, 46.70, 10.60, 13.15)),
    "FVG": ("Friuli-Venezia Giulia", 46.07, 13.24, (45.55, 46.70, 12.30, 13.95)),
    "EMR": ("Emilia-Romagna", 44.49, 11.34, (43.70, 45.15, 9.15, 12.85)),

    "TOS": ("Toscana", 43.77, 11.25, (42.20, 44.55, 9.65, 12.40)),
    "UMB": ("Umbria", 43.11, 12.39, (42.35, 43.65, 11.85, 13.30)),
    "MAR": ("Marche", 43.62, 13.52, (42.65, 44.00, 12.15, 13.95)),
    "LAZ": ("Lazio", 41.90, 12.50, (40.75, 42.85, 11.40, 14.05)),

    "ABR": ("Abruzzo", 42.35, 13.40, (41.65, 42.95, 13.00, 14.85)),
    "MOL": ("Molise", 41.56, 14.66, (41.30, 42.10, 13.90, 15.20)),
    "CAM": ("Campania", 40.85, 14.27, (39.95, 41.55, 13.70, 15.85)),
    "PUG": ("Puglia", 41.12, 16.87, (39.70, 42.15, 14.90, 18.55)),
    "BAS": ("Basilicata", 40.64, 15.80, (39.85, 41.20, 15.30, 16.90)),
    "CAL": ("Calabria", 38.91, 16.59, (37.85, 40.15, 15.55, 17.25)),

    "SIC": ("Sicilia", 37.50, 14.00, (36.55, 38.85, 11.90, 15.75)),
    "SAR": ("Sardegna", 40.12, 9.01, (38.75, 41.35, 8.00, 9.90)),
}

PREFERENZA_CANALI = [
    "HHZ",
    "EHZ",
    "BHZ",
    "HNZ",
    "ENZ",
    "SHZ"
]


def distanza(lat1, lon1, lat2, lon2):
    r = 6371.0

    a1 = math.radians(lat1)
    a2 = math.radians(lat2)

    da = math.radians(lat2 - lat1)
    do = math.radians(lon2 - lon1)

    a = (
        math.sin(da / 2) ** 2
        + math.cos(a1)
        * math.cos(a2)
        * math.sin(do / 2) ** 2
    )

    return 2 * r * math.asin(math.sqrt(a))


def trova_canali(station):
    url = (
        "https://webservices.ingv.it/fdsnws/station/1/query"
        f"?network=IV"
        f"&station={station}"
        f"&level=channel"
        f"&format=text"
    )

    try:
        r = requests.get(url, timeout=15)

        if r.status_code != 200:
            return []

        disponibili = set()

        for riga in r.text.splitlines():
            if not riga or riga.startswith("#"):
                continue

            parti = riga.split("|")

            if len(parti) < 17:
                continue

            channel = parti[3].strip()
            endtime = parti[16].strip()

            # solo canali ancora aperti
            if not endtime:
                disponibili.add(channel)

        return [
            c
            for c in PREFERENZA_CANALI
            if c in disponibili
        ]

    except Exception:
        return []


def verifica_dati(station, channel):
    fine = datetime.now(timezone.utc)
    inizio = fine - timedelta(minutes=30)

    start = inizio.strftime("%Y-%m-%dT%H:%M:%S")
    end = fine.strftime("%Y-%m-%dT%H:%M:%S")

    url = (
        "https://webservices.ingv.it/fdsnws/dataselect/1/query"
        f"?net=IV"
        f"&sta={station}"
        f"&loc=--"
        f"&cha={channel}"
        f"&starttime={start}"
        f"&endtime={end}"
        f"&nodata=404"
    )

    try:
        r = requests.get(url, timeout=20)

        return (
            r.status_code == 200
            and len(r.content) > 1000
        )

    except Exception:
        return False


with open("stazioni_iv.json", encoding="utf-8") as f:
    stazioni = json.load(f)


risultati = {}

print()
print("🇮🇹 RICERCA STAZIONI REGIONALI ATTIVE")
print("=" * 65)

for codice, info in REGIONI.items():

    nome, centro_lat, centro_lon, limiti = info

    minlat, maxlat, minlon, maxlon = limiti

    candidati = []

    for s in stazioni:
        lat = float(s["latitude"])
        lon = float(s["longitude"])

        if not (
            minlat <= lat <= maxlat
            and minlon <= lon <= maxlon
        ):
            continue

        km = distanza(
            centro_lat,
            centro_lon,
            lat,
            lon
        )

        candidati.append(
            (km, s)
        )

    candidati.sort(key=lambda x: x[0])

    print()
    print(f"📍 {nome}")

    trovato = None

    # proviamo le 6 più vicine
    for km, s in candidati[:6]:

        sta = s["station"]

        canali = trova_canali(sta)

        if not canali:
            continue

        for cha in canali:

            print(
                f"   Provo IV.{sta}..{cha}",
                end=" ... ",
                flush=True
            )

            if verifica_dati(sta, cha):
                print("✅")

                trovato = {
                    "region": nome,
                    "station": sta,
                    "channel": cha,
                    "name": s.get("name", ""),
                    "latitude": s["latitude"],
                    "longitude": s["longitude"],
                    "distance_km": round(km, 1)
                }

                break

            print("no dati")

        if trovato:
            break

    if trovato:

        risultati[codice] = trovato

        print(
            f"   ✅ SCELTA: "
            f"IV.{trovato['station']}..{trovato['channel']}"
        )

        print(
            f"      {trovato['name']}"
        )

    else:

        print(
            "   ❌ Nessuna stazione con dati recenti trovata"
        )


with open(
    "stazioni_regioni.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        risultati,
        f,
        indent=2,
        ensure_ascii=False
    )


print()
print("=" * 65)
print(
    f"✅ Regioni trovate: "
    f"{len(risultati)}/20"
)
print(
    "✅ Salvato: stazioni_regioni.json"
)
