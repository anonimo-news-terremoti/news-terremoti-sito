from flask import Flask, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta, timezone
import os
import requests
import numpy as np
from obspy import read

app = Flask(__name__, static_folder=".")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
utenti_online = 0

STAZIONI = {
    "CSFT": {"channel": "HHZ", "name": "Solfatara"},
    "CPIS": {"channel": "HHZ", "name": "Pisciarelli"},
    "CBAG": {"channel": "HHZ", "name": "Bagnoli"},
    "CNIS": {"channel": "HHZ", "name": "Nisida"},
    "CFMN": {"channel": "HHZ", "name": "Monte Nuovo"},
    "OVO":  {"channel": "HHZ", "name": "Vesuvio"},

    "MRGE": {"channel": "HHZ", "name": "Valle d'Aosta"},
    "MONC": {"channel": "HHZ", "name": "Piemonte"},
    "QLNO": {"channel": "HHZ", "name": "Liguria"},
    "MILN": {"channel": "HHZ", "name": "Lombardia"},
    "APPI": {"channel": "EHZ", "name": "Trentino-Alto Adige"},
    "VENL": {"channel": "EHZ", "name": "Veneto"},
    "STAL": {"channel": "HHZ", "name": "Friuli-Venezia Giulia"},
    "FIU":  {"channel": "EHZ", "name": "Emilia-Romagna"},
    "FIR":  {"channel": "HHZ", "name": "Toscana"},
    "MURB": {"channel": "HHZ", "name": "Umbria"},

    "AOI":  {"channel": "HHZ", "name": "Marche"},
    "ROM9": {"channel": "HNZ", "name": "Lazio"},
    "FAGN": {"channel": "HHZ", "name": "Abruzzo"},
    "BSSO": {"channel": "HHZ", "name": "Molise"},
    "CMTS": {"channel": "EHZ", "name": "Campania"},
    "AMUR": {"channel": "HHZ", "name": "Puglia"},
    "PZUN": {"channel": "HHZ", "name": "Basilicata"},
    "SELL": {"channel": "HHZ", "name": "Calabria"},
    "RESU": {"channel": "HHZ", "name": "Sicilia"},
    "BULT": {"channel": "EHZ", "name": "Sardegna"},
}


def scarica(station, channel):
    fine = datetime.now(timezone.utc)
    inizio = fine - timedelta(minutes=5)

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

    r = requests.get(url, timeout=30)

    if r.status_code != 200 or not r.content:
        raise RuntimeError(f"Nessun dato per {station}")

    nome = f"/tmp/{station}_{channel}.mseed"

    with open(nome, "wb") as f:
        f.write(r.content)

    return nome


def prepara_dati(file_mseed):
    st = read(file_mseed)
    st.merge(method=1, fill_value="interpolate")

    tr = st[0]
    tr.detrend("demean")

    dati = tr.data.astype(float)

    # Riduce il numero di punti per il browser
    max_punti = 1200

    if len(dati) > max_punti:
        passo = max(1, len(dati) // max_punti)
        dati = dati[::passo]

    # Normalizzazione per visualizzazione
    max_abs = np.max(np.abs(dati))

    if max_abs > 0:
        dati = dati / max_abs

    return dati.tolist()



STAZIONI_MONDO = {
    "GRECIA": {
        "source": "GEOFON",
        "base": "https://geofon.gfz.de/fdsnws",
        "net": "GE", "sta": "APE", "loc": "*", "cha": "HHZ"
    },
    "ISLANDA": {
        "source": "GEOFON",
        "base": "https://geofon.gfz.de/fdsnws",
        "net": "GE", "sta": "SUMG", "loc": "*", "cha": "BHZ"
    },
    "TURCHIA": {
        "source": "GEOFON",
        "base": "https://geofon.gfz.de/fdsnws",
        "net": "GE", "sta": "KARP", "loc": "*", "cha": "BHZ"
    },
    "SPAGNA": {
        "source": "GEOFON",
        "base": "https://geofon.gfz.de/fdsnws",
        "net": "GE", "sta": "MTE", "loc": "*", "cha": "HHZ"
    },

    "CALIFORNIA": {
        "source": "SCEDC",
        "base": "https://service.scedc.caltech.edu/fdsnws",
        "net": "CI", "sta": "SBC", "loc": "*", "cha": "HHZ"
    },
    "MESSICO": {
        "source": "IRIS",
        "base": "https://service.iris.edu/fdsnws",
        "net": "IU", "sta": "TEIG", "loc": "00", "cha": "BHZ"
    },
    "CILE": {
        "source": "IRIS",
        "base": "https://service.iris.edu/fdsnws",
        "net": "IU", "sta": "LCO", "loc": "00", "cha": "BHZ"
    },
    "VENEZUELA": {
        "source": "IRIS",
        "base": "https://service.iris.edu/fdsnws",
        "net": "IU", "sta": "SDV", "loc": "00", "cha": "BHZ"
    },

    "GIAPPONE": {
        "source": "IRIS",
        "base": "https://service.iris.edu/fdsnws",
        "net": "IU", "sta": "MAJO", "loc": "00", "cha": "BHZ"
    },
    "INDONESIA": {
        "source": "GEOFON",
        "base": "https://geofon.gfz.de/fdsnws",
        "net": "GE", "sta": "JAGI", "loc": "*", "cha": "BHZ"
    },
    "PAPUA": {
        "source": "GEOFON",
        "base": "https://geofon.gfz.de/fdsnws",
        "net": "GE", "sta": "PMG", "loc": "*", "cha": "BHZ"
    },
    "NUOVAZELANDA": {
        "source": "IRIS",
        "base": "https://service.iris.edu/fdsnws",
        "net": "IU", "sta": "SNZO", "loc": "00", "cha": "BHZ"
    },

    "ETIOPIA": {
        "source": "GEOFON",
        "base": "https://geofon.gfz.de/fdsnws",
        "net": "GE", "sta": "DAMY", "loc": "*", "cha": "HHZ"
    },
    "SUDAFRICA": {
        "source": "GEOFON",
        "base": "https://geofon.gfz.de/fdsnws",
        "net": "GE", "sta": "WIN", "loc": "*", "cha": "HHZ"
    },
}


@app.route("/api/sismografo/<station>")
def api_sismografo(station):
    station = station.upper()

    if station not in STAZIONI:
        return jsonify({"error": "Stazione non valida"}), 404

    info = STAZIONI[station]

    try:
        file_mseed = scarica(
            station,
            info["channel"]
        )

        dati = prepara_dati(file_mseed)

        return jsonify({
            "station": station,
            "channel": info["channel"],
            "name": info["name"],
            "updated": datetime.now().astimezone().isoformat(),
            "samples": dati
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500



@socketio.on("connect")
def chat_connect():
    global utenti_online
    utenti_online += 1
    emit("online_count", utenti_online, broadcast=True)


@socketio.on("disconnect")
def chat_disconnect():
    global utenti_online
    utenti_online = max(0, utenti_online - 1)
    emit("online_count", utenti_online, broadcast=True)


@socketio.on("join_chat")
def join_chat(data):
    nickname = str(data.get("nickname", "")).strip()[:25]

    if not nickname:
        return

    emit(
        "chat_message",
        {
            "nickname": "Sistema",
            "message": f"{nickname} è entrato/a nella chat.",
            "time": datetime.now().astimezone().strftime("%H:%M")
        },
        broadcast=True
    )


@socketio.on("chat_message")
def chat_message(data):
    nickname = str(data.get("nickname", "")).strip()[:25]
    message = str(data.get("message", "")).strip()[:500]

    if not nickname or not message:
        return

    emit(
        "chat_message",
        {
            "nickname": nickname,
            "message": message,
            "time": datetime.now().astimezone().strftime("%H:%M")
        },
        broadcast=True
    )


@app.route("/")
def home():
    return send_from_directory(".", "sismografi.html")


@app.route("/<path:path>")
def files(path):
    return send_from_directory(".", path)




@app.route("/api/sismografo-mondo/<codice>")
def api_sismografo_mondo(codice):
    import io
    import requests
    import numpy as np
    from datetime import datetime, timedelta, timezone
    from obspy import read

    codice = codice.upper()

    cfg = STAZIONI_MONDO.get(codice)

    if not cfg:
        return {"error": "Stazione mondo non trovata"}, 404

    fine = datetime.now(timezone.utc)
    inizio = fine - timedelta(minutes=5)

    params = {
        "net": cfg["net"],
        "sta": cfg["sta"],
        "loc": cfg["loc"],
        "cha": cfg["cha"],
        "starttime": inizio.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": fine.strftime("%Y-%m-%dT%H:%M:%S"),
        "nodata": 404
    }

    url = cfg["base"] + "/dataselect/1/query"

    try:
        r = requests.get(
            url,
            params=params,
            timeout=20,
            headers={"User-Agent": "NewsTerremotiMonitor/1.0"}
        )

        if r.status_code != 200:
            return {
                "error": "Dati non disponibili",
                "http": r.status_code
            }, 502

        st = read(io.BytesIO(r.content))

        if not st:
            return {"error": "Nessun tracciato"}, 502

        tr = st[0]

        dati = tr.data.astype(float)

        if len(dati) < 2:
            return {"error": "Campioni insufficienti"}, 502

        dati = dati - np.mean(dati)

        max_abs = np.max(np.abs(dati))

        if max_abs > 0:
            dati = dati / max_abs

        massimo_punti = 1200

        if len(dati) > massimo_punti:
            indici = np.linspace(
                0,
                len(dati) - 1,
                massimo_punti
            ).astype(int)

            dati = dati[indici]

        return {
            "code": codice,
            "source": cfg["source"],
            "network": cfg["net"],
            "station": cfg["sta"],
            "location": cfg["loc"],
            "channel": cfg["cha"],
            "samples": dati.tolist()
        }

    except Exception as e:
        return {
            "error": str(e)
        }, 500




@app.route("/api/ultimi-terremoti-mondo")
def api_ultimi_terremoti_mondo():
    import requests
    from datetime import datetime, timedelta, timezone

    fine = datetime.now(timezone.utc)
    inizio = fine - timedelta(hours=24)

    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query"
    )

    params = {
        "format": "geojson",
        "starttime": inizio.isoformat(),
        "endtime": fine.isoformat(),
        "minmagnitude": 3.5,
        "orderby": "time",
        "limit": 3
    }

    try:
        r = requests.get(
            url,
            params=params,
            timeout=20,
            headers={
                "User-Agent":
                    "NewsTerremotiMonitor/1.0"
            }
        )

        if r.status_code != 200:
            return {
                "error": "USGS non disponibile",
                "http": r.status_code
            }, 502

        return r.json()

    except Exception as e:
        return {
            "error": str(e)
        }, 500




@app.route("/api/ultimi-terremoti-italia")
def api_ultimi_terremoti_italia():

    import requests
    from datetime import datetime, timedelta, timezone

    fine = datetime.now(timezone.utc)
    inizio = fine - timedelta(hours=24)

    url = (
        "https://webservices.ingv.it/"
        "fdsnws/event/1/query"
    )

    params = {
        "format": "geojson",

        "starttime":
            inizio.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),

        "endtime":
            fine.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),

        "minlatitude": 35,
        "maxlatitude": 47.5,

        "minlongitude": 6,
        "maxlongitude": 19,

        "minmagnitude": 1.5,

        "orderby": "time",

        "limit": 100,

        "nodata": 404
    }

    try:

        r = requests.get(
            url,
            params=params,
            timeout=20,
            headers={
                "User-Agent":
                    "NewsTerremotiMonitor/1.0"
            }
        )

        if r.status_code != 200:

            return {
                "error":
                    "INGV non disponibile",
                "http":
                    r.status_code
            }, 502

        dati = r.json()

        eventi = dati.get(
            "features",
            []
        )

        # Ordina dal più recente
        eventi.sort(
            key=lambda evento:
                evento.get(
                    "properties",
                    {}
                ).get(
                    "time",
                    ""
                ),
            reverse=True
        )

        # Ultimi 10
        eventi = eventi[:10]

        return {
            "type":
                "FeatureCollection",

            "features":
                eventi
        }

    except Exception as e:

        return {
            "error":
                str(e)
        }, 500


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(__import__("os").environ.get("PORT", 8090)),
        debug=False,
        allow_unsafe_werkzeug=True
    )
