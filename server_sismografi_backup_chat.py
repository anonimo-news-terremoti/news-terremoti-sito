from flask import Flask, jsonify, send_from_directory
from datetime import datetime, timedelta, timezone
import os
import requests
import numpy as np
from obspy import read

app = Flask(__name__, static_folder=".")

STAZIONI = {
    "CSFT": {"channel": "HHZ", "name": "Solfatara"},
    "CPIS": {"channel": "HHZ", "name": "Pisciarelli"},
    "CBAG": {"channel": "HHZ", "name": "Bagnoli"},
    "CNIS": {"channel": "HHZ", "name": "Nisida"},
    "CFMN": {"channel": "HHZ", "name": "Monte Nuovo"},
    "OVO":  {"channel": "HHZ", "name": "Vesuvio"},
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


@app.route("/")
def home():
    return send_from_directory(".", "sismografi.html")


@app.route("/<path:path>")
def files(path):
    return send_from_directory(".", path)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8090,
        debug=False
    )
