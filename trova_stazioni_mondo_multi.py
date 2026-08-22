import json
import math
import requests
from datetime import datetime, timedelta, timezone

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

SERVERS = {
    "GEOFON": "https://geofon.gfz.de/fdsnws",
    "ORFEUS": "https://www.orfeus-eu.org/fdsnws",
    "IRIS": "https://service.iris.edu/fdsnws",
    "INGV": "https://webservices.ingv.it/fdsnws",
}

PREFERENZA_CANALI = [
    "HHZ",
    "BHZ",
    "EHZ",
    "SHZ",
    "HNZ",
    "ENZ"
]

headers = {
    "User-Agent": "NewsTerremotiMonitor/1.0"
}


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


def cerca_stazioni(server, bbox):
    minlat, maxlat, minlon, maxlon = bbox

    url = server + "/station/1/query"

    params = {
        "minlatitude": minlat,
        "maxlatitude": maxlat,
        "minlongitude": minlon,
        "maxlongitude": maxlon,
        "level": "channel",
        "format": "text"
    }

    r = requests.get(
        url,
        params=params,
        timeout=20,
        headers=headers
    )

    if r.status_code != 200:
        return []

    stazioni = {}

    for riga in r.text.splitlines():
        if not riga or riga.startswith("#"):
            continue

        parti = riga.split("|")

        if len(parti) < 6:
            continue

        net = parti[0].strip()
        sta = parti[1].strip()
        loc = parti[2].strip()
        cha = parti[3].strip()

        try:
            lat = float(parti[4])
            lon = float(parti[5])
        except Exception:
            continue

        key = (net, sta, loc)

        if key not in stazioni:
            stazioni[key] = {
                "network": net,
                "station": sta,
                "location": loc,
                "latitude": lat,
                "longitude": lon,
                "channels": set()
            }

        stazioni[key]["channels"].add(cha)

    return list(stazioni.values())


def canale_preferito(canali):
    for c in PREFERENZA_CANALI:
        if c in canali:
            return c

    for c in canali:
        if c.endswith("Z"):
            return c

    return None


def verifica_dati(server, net, sta, loc, cha):
    fine = datetime.now(timezone.utc)
    inizio = fine - timedelta(minutes=30)

    url = server + "/dataselect/1/query"

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
            url,
            params=params,
            timeout=20,
            headers=headers
        )

        return (
            r.status_code == 200
            and len(r.content) > 1000
        )

    except Exception:
        return False


# Manteniamo le 3 già trovate
risultati = {
    "PAPUA": {
        "zone": "Papua Nuova Guinea",
        "server_name": "GEOFON",
        "server": SERVERS["GEOFON"],
        "network": "GE",
        "station": "PMG",
        "location": "",
        "channel": "BHZ"
    },
    "ETIOPIA": {
        "zone": "Etiopia",
        "server_name": "GEOFON",
        "server": SERVERS["GEOFON"],
        "network": "GE",
        "station": "DAMY",
        "location": "",
        "channel": "HHZ"
    },
    "SUDAFRICA": {
        "zone": "Sudafrica",
        "server_name": "GEOFON",
        "server": SERVERS["GEOFON"],
        "network": "GE",
        "station": "WIN",
        "location": "",
        "channel": "HHZ"
    }
}

print()
print("🌍 RICERCA MULTI-SERVER STAZIONI MONDO")
print("=" * 74)

for codice, info in ZONE.items():

    if codice in risultati:
        print()
        print(f"📍 {info[0]}")
        r = risultati[codice]

        print(
            "   ✅ GIÀ DISPONIBILE:",
            f'{r["network"]}.{r["station"]}.--.{r["channel"]}',
            f'[{r["server_name"]}]'
        )
        continue

    nome, centro_lat, centro_lon, bbox = info

    print()
    print(f"📍 {nome}")

    trovato = None

    for server_name, server in SERVERS.items():

        print(f"   🔎 Server: {server_name}")

        try:
            stazioni = cerca_stazioni(
                server,
                bbox
            )
        except Exception as e:
            print(
                "      ⚠️ ricerca fallita:",
                type(e).__name__
            )
            continue

        candidati = []

        for s in stazioni:
            cha = canale_preferito(
                s["channels"]
            )

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

        candidati.sort(
            key=lambda x: x[0]
        )

        for km, s, cha in candidati[:15]:

            net = s["network"]
            sta = s["station"]
            loc = s["location"]

            loc_vis = loc or "--"

            print(
                f"      Provo "
                f"{net}.{sta}.{loc_vis}.{cha}",
                end=" ... ",
                flush=True
            )

            if verifica_dati(
                server,
                net,
                sta,
                loc,
                cha
            ):
                print("✅")

                trovato = {
                    "zone": nome,
                    "server_name": server_name,
                    "server": server,
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
            break

    if trovato:

        risultati[codice] = trovato

        loc_vis =
            trovato["location"] or "--"

        print(
            "   ✅ SCELTA FINALE:",
            f'{trovato["network"]}.'
            f'{trovato["station"]}.'
            f'{loc_vis}.'
            f'{trovato["channel"]}',
            f'[{trovato["server_name"]}]'
        )

    else:

        print(
            "   ❌ Nessuna stazione attiva trovata"
        )


with open(
    "stazioni_mondo_multi.json",
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
print("=" * 74)
print(
    f"✅ Zone trovate: "
    f"{len(risultati)}/{len(ZONE)}"
)
print(
    "✅ Salvato: stazioni_mondo_multi.json"
)
