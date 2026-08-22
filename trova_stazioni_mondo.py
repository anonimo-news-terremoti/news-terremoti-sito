import math
import json
import requests
from datetime import datetime, timedelta, timezone

# Zone indicative da coprire
ZONE = {
    "GRECIA": ("Grecia", 38.5, 23.7, (34.5, 42.0, 19.0, 30.0)),
    "ISLANDA": ("Islanda", 64.8, -18.0, (63.0, 67.5, -25.0, -13.0)),
    "TURCHIA": ("Turchia", 39.0, 35.0, (35.5, 42.5, 25.5, 45.0)),
    "SPAGNA": ("Spagna", 40.3, -3.7, (35.5, 44.5, -10.0, 4.5)),

    "CALIFORNIA": ("California", 36.5, -119.5, (32.0, 42.5, -125.0, -113.0)),
    "MESSICO": ("Messico", 23.6, -102.5, (14.0, 33.0, -118.0, -86.0)),
    "CILE": ("Cile", -33.0, -71.0, (-56.0, -17.0, -76.0, -66.0)),
    "VENEZUELA": ("Venezuela", 8.0, -66.0, (0.0, 13.0, -74.0, -59.0)),

    "GIAPPONE": ("Giappone", 36.2, 138.2, (30.0, 46.0, 128.0, 146.0)),
    "INDONESIA": ("Indonesia", -2.0, 118.0, (-11.0, 6.5, 95.0, 141.0)),
    "PAPUA": ("Papua Nuova Guinea", -6.0, 147.0, (-12.0, 1.0, 140.0, 156.0)),
    "NUOVAZELANDA": ("Nuova Zelanda", -41.0, 174.0, (-48.0, -33.0, 165.0, 179.9)),

    "ETIOPIA": ("Etiopia", 9.0, 40.5, (3.0, 15.0, 33.0, 48.0)),
    "SUDAFRICA": ("Sudafrica", -30.5, 24.0, (-35.0, -22.0, 16.0, 33.0)),
}

PREFERENZA_CANALI = [
    "HHZ",
    "BHZ",
    "EHZ",
    "SHZ",
    "HNZ"
]

STATION_URL = "https://geofon.gfz.de/fdsnws/station/1/query"
DATA_URL = "https://geofon.gfz.de/fdsnws/dataselect/1/query"


def distanza(lat1, lon1, lat2, lon2):
    r = 6371.0

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dl / 2) ** 2
    )

    return 2 * r * math.asin(math.sqrt(a))


def cerca_stazioni(bbox):
    minlat, maxlat, minlon, maxlon = bbox

    params = {
        "minlatitude": minlat,
        "maxlatitude": maxlat,
        "minlongitude": minlon,
        "maxlongitude": maxlon,
        "level": "channel",
        "format": "text"
    }

    r = requests.get(
        STATION_URL,
        params=params,
        timeout=25,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    if r.status_code != 200:
        return []

    stazioni = {}

    for riga in r.text.splitlines():
        if not riga or riga.startswith("#"):
            continue

        parti = riga.split("|")

        if len(parti) < 17:
            continue

        network = parti[0].strip()
        station = parti[1].strip()
        location = parti[2].strip()
        channel = parti[3].strip()

        try:
            lat = float(parti[4])
            lon = float(parti[5])
        except Exception:
            continue

        key = (network, station, location)

        if key not in stazioni:
            stazioni[key] = {
                "network": network,
                "station": station,
                "location": location,
                "latitude": lat,
                "longitude": lon,
                "channels": set()
            }

        stazioni[key]["channels"].add(channel)

    return list(stazioni.values())


def canale_preferito(channels):
    for cha in PREFERENZA_CANALI:
        if cha in channels:
            return cha

    # fallback: qualsiasi verticale
    for cha in channels:
        if cha.endswith("Z"):
            return cha

    return None


def verifica_dati(net, sta, loc, cha):
    fine = datetime.now(timezone.utc)
    inizio = fine - timedelta(minutes=30)

    params = {
        "net": net,
        "sta": sta,
        "loc": loc if loc else "*",
        "cha": cha,
        "starttime": inizio.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": fine.strftime("%Y-%m-%dT%H:%M:%S"),
        "nodata": 404
    }

    try:
        r = requests.get(
            DATA_URL,
            params=params,
            timeout=25,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        return (
            r.status_code == 200
            and len(r.content) > 1000
        )

    except Exception:
        return False


risultati = {}

print()
print("🌍 RICERCA STAZIONI MONDIALI ATTIVE")
print("=" * 70)

for codice, info in ZONE.items():

    nome, centro_lat, centro_lon, bbox = info

    print()
    print(f"📍 {nome}")

    try:
        stazioni = cerca_stazioni(bbox)
    except Exception as e:
        print("   ❌ Errore ricerca stazioni:", e)
        continue

    candidati = []

    for s in stazioni:
        cha = canale_preferito(s["channels"])

        if not cha:
            continue

        km = distanza(
            centro_lat,
            centro_lon,
            s["latitude"],
            s["longitude"]
        )

        candidati.append(
            (km, s, cha)
        )

    candidati.sort(key=lambda x: x[0])

    trovato = None

    # prova fino a 12 candidati
    for km, s, cha in candidati[:12]:

        net = s["network"]
        sta = s["station"]
        loc = s["location"]

        loc_vis = loc if loc else "--"

        print(
            f"   Provo {net}.{sta}.{loc_vis}.{cha}",
            end=" ... ",
            flush=True
        )

        if verifica_dati(net, sta, loc, cha):
            print("✅")

            trovato = {
                "zone": nome,
                "network": net,
                "station": sta,
                "location": loc,
                "channel": cha,
                "latitude": s["latitude"],
                "longitude": s["longitude"],
                "distance_km": round(km, 1)
            }

            break

        print("no dati")

    if trovato:
        risultati[codice] = trovato

        loc_vis = trovato["location"] or "--"

        print(
            "   ✅ SCELTA:",
            f'{trovato["network"]}.'
            f'{trovato["station"]}.'
            f'{loc_vis}.'
            f'{trovato["channel"]}'
        )

    else:
        print(
            "   ❌ Nessuna stazione con dati recenti trovata"
        )


with open(
    "stazioni_mondo.json",
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
print("=" * 70)
print(
    f"✅ Zone trovate: {len(risultati)}/{len(ZONE)}"
)
print("✅ Salvato: stazioni_mondo.json")
